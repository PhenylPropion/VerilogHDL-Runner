use eframe::egui;
use egui::{RichText, ScrollArea, TextEdit};
use regex::Regex;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use walkdir::WalkDir;

fn main() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([1200.0, 750.0])
            .with_title("Verilog HDL Runner"),
        ..Default::default()
    };

    eframe::run_native(
        "Verilog HDL Runner",
        options,
        Box::new(|cc| {
            // フォント設定
            let mut fonts = egui::FontDefinitions::default();
            
            // 日本語フォントを追加（システムフォントを使用）
            #[cfg(target_os = "macos")]
            {
                if let Ok(font_data) = std::fs::read("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc") {
                    fonts.font_data.insert(
                        "HiraginoSans".to_owned(),
                        egui::FontData::from_owned(font_data),
                    );
                    
                    fonts.families.entry(egui::FontFamily::Proportional)
                        .or_default()
                        .insert(0, "HiraginoSans".to_owned());
                        
                    fonts.families.entry(egui::FontFamily::Monospace)
                        .or_default()
                        .insert(0, "HiraginoSans".to_owned());
                }
            }
            
            cc.egui_ctx.set_fonts(fonts);
            
            // スタイル設定
            let mut style = (*cc.egui_ctx.style()).clone();
            style.spacing.item_spacing = egui::vec2(8.0, 6.0);
            cc.egui_ctx.set_style(style);
            
            Ok(Box::<VerilogRunnerApp>::default())
        }),
    )
}

struct VerilogRunnerApp {
    current_dir: PathBuf,
    selected_directory: PathBuf,
    folder_tree: Vec<FolderNode>,
    testbench_files: Vec<String>,
    dependency_files: Vec<DependencyFile>,
    selected_testbench: Option<usize>,
    output_log: Arc<Mutex<String>>,
    gtkwave_enabled: bool,
    auto_detect_enabled: bool,
    running: Arc<Mutex<bool>>,
}

#[derive(Clone)]
struct FolderNode {
    name: String,
    path: PathBuf,
    children: Vec<FolderNode>,
    expanded: bool,
}

#[derive(Clone)]
struct DependencyFile {
    name: String,
    checked: bool,
}

impl VerilogRunnerApp {
    fn new() -> Self {
        let current_dir = std::env::current_dir().unwrap_or_default();
        let selected_directory = current_dir.clone();

        let mut app = Self {
            current_dir: current_dir.clone(),
            selected_directory,
            folder_tree: Vec::new(),
            testbench_files: Vec::new(),
            dependency_files: Vec::new(),
            selected_testbench: None,
            output_log: Arc::new(Mutex::new(String::new())),
            gtkwave_enabled: true,
            auto_detect_enabled: true,
            running: Arc::new(Mutex::new(false)),
        };

        app.refresh_folder_tree();
        app.update_testbench_list();
        app
    }

    fn refresh_folder_tree(&mut self) {
        self.folder_tree.clear();
        if self.current_dir.exists() {
            let root_name = self
                .current_dir
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("Root")
                .to_string();

            let node = FolderNode {
                name: root_name,
                path: self.current_dir.clone(),
                children: self.build_folder_tree(&self.current_dir),
                expanded: true,
            };
            self.folder_tree.push(node);
        }
        self.log_message("ディレクトリを更新しました\n", LogLevel::Success);
    }

    fn build_folder_tree(&self, dir: &Path) -> Vec<FolderNode> {
        let mut nodes = Vec::new();

        if let Ok(entries) = fs::read_dir(dir) {
            let mut dirs: Vec<_> = entries
                .filter_map(|e| e.ok())
                .filter(|e| {
                    e.path().is_dir()
                        && !e
                            .file_name()
                            .to_str()
                            .map(|s| s.starts_with('.'))
                            .unwrap_or(true)
                })
                .collect();

            dirs.sort_by_key(|e| e.file_name());

            for entry in dirs {
                let path = entry.path();
                if self.has_verilog_files(&path) {
                    let name = entry.file_name().to_string_lossy().to_string();
                    nodes.push(FolderNode {
                        name,
                        path: path.clone(),
                        children: self.build_folder_tree(&path),
                        expanded: false,
                    });
                }
            }
        }

        nodes
    }

    fn has_verilog_files(&self, dir: &Path) -> bool {
        WalkDir::new(dir)
            .max_depth(3)
            .into_iter()
            .filter_map(|e| e.ok())
            .any(|e| {
                e.path()
                    .extension()
                    .and_then(|ext| ext.to_str())
                    .map(|ext| ext == "v")
                    .unwrap_or(false)
            })
    }

    fn update_testbench_list(&mut self) {
        self.testbench_files.clear();
        self.dependency_files.clear();
        self.selected_testbench = None;

        if let Ok(entries) = fs::read_dir(&self.selected_directory) {
            let mut files: Vec<_> = entries
                .filter_map(|e| e.ok())
                .filter(|e| {
                    e.path()
                        .file_name()
                        .and_then(|n| n.to_str())
                        .map(|s| s.ends_with("_tb.v"))
                        .unwrap_or(false)
                })
                .collect();

            files.sort_by_key(|e| e.file_name());

            for entry in files {
                if let Some(name) = entry.file_name().to_str() {
                    self.testbench_files.push(name.to_string());
                }
            }
        }
    }

    fn detect_dependencies(&mut self, tb_file: &str) {
        let tb_path = self.selected_directory.join(tb_file);
        let mut dependencies = HashSet::new();

        if let Ok(content) = fs::read_to_string(&tb_path) {
            // モジュールインスタンス化パターン
            let re = Regex::new(r"^\s*(\w+)\s+\w+\s*\(").unwrap();
            
            for line in content.lines() {
                if let Some(caps) = re.captures(line) {
                    let module_name = &caps[1];
                    
                    // 予約語を除外
                    let keywords = [
                        "module", "initial", "always", "assign", "wire", "reg", 
                        "integer", "input", "output", "inout", "parameter"
                    ];
                    
                    if !keywords.contains(&module_name) {
                        let module_file = format!("{}.v", module_name);
                        let module_path = self.selected_directory.join(&module_file);
                        
                        if module_path.exists() {
                            dependencies.insert(module_file);
                        }
                    }
                }
            }

            // メインモジュールを追加
            let main_module = tb_file.replace("_tb.v", ".v");
            let main_path = self.selected_directory.join(&main_module);
            if main_path.exists() {
                dependencies.insert(main_module);
            }
        }

        self.update_dependency_list(Some(dependencies));
    }

    fn update_dependency_list(&mut self, auto_detected: Option<HashSet<String>>) {
        self.dependency_files.clear();

        if let Ok(entries) = fs::read_dir(&self.selected_directory) {
            let mut files: Vec<_> = entries
                .filter_map(|e| e.ok())
                .filter(|e| {
                    e.path()
                        .file_name()
                        .and_then(|n| n.to_str())
                        .map(|s| s.ends_with(".v") && !s.ends_with("_tb.v"))
                        .unwrap_or(false)
                })
                .collect();

            files.sort_by_key(|e| e.file_name());

            for entry in files {
                if let Some(name) = entry.file_name().to_str() {
                    let checked = auto_detected
                        .as_ref()
                        .map(|deps| deps.contains(name))
                        .unwrap_or(false);

                    self.dependency_files.push(DependencyFile {
                        name: name.to_string(),
                        checked,
                    });
                }
            }
        }
    }

    fn run_verilog(&mut self) {
        if let Some(idx) = self.selected_testbench {
            if idx < self.testbench_files.len() {
                let tb_file = self.testbench_files[idx].clone();
                let dep_files: Vec<String> = self
                    .dependency_files
                    .iter()
                    .filter(|d| d.checked)
                    .map(|d| d.name.clone())
                    .collect();

                if dep_files.is_empty() {
                    self.log_message(
                        "[WARN] 依存ファイルが選択されていません\n",
                        LogLevel::Warning,
                    );
                }

                let directory = self.selected_directory.clone();
                let output_log = Arc::clone(&self.output_log);
                let running = Arc::clone(&self.running);
                let gtkwave_enabled = self.gtkwave_enabled;

                *running.lock().unwrap() = true;

                thread::spawn(move || {
                    run_verilog_thread(
                        &tb_file,
                        &dep_files,
                        &directory,
                        output_log,
                        gtkwave_enabled,
                    );
                    *running.lock().unwrap() = false;
                });
            }
        }
    }

    fn log_message(&self, message: &str, _level: LogLevel) {
        let mut log = self.output_log.lock().unwrap();
        log.push_str(message);
    }

    fn select_all_deps(&mut self) {
        for dep in &mut self.dependency_files {
            dep.checked = true;
        }
    }

    fn deselect_all_deps(&mut self) {
        for dep in &mut self.dependency_files {
            dep.checked = false;
        }
    }
}

#[derive(Clone, Copy)]
#[allow(dead_code)]
enum LogLevel {
    Success,
    Error,
    Warning,
    Info,
    Header,
}

fn run_verilog_thread(
    tb_file: &str,
    dep_files: &[String],
    directory: &Path,
    output_log: Arc<Mutex<String>>,
    gtkwave_enabled: bool,
) {
    let name = tb_file.replace("_tb.v", "");

    // ログヘッダー
    log_to_output(
        &output_log,
        &format!("\n{}\n[開始] {} の実行\n{}\n\n", "=".repeat(60), name, "=".repeat(60)),
    );
    log_to_output(
        &output_log,
        &format!("[DIR] 作業ディレクトリ: {:?}\n", directory),
    );
    log_to_output(&output_log, &format!("[TB] テストベンチ: {}\n", tb_file));
    log_to_output(
        &output_log,
        &format!("[DEP] 依存ファイル: {}\n\n", dep_files.join(", ")),
    );

    // iverilog実行
    let mut cmd_args = vec!["-Wall", "-o", &name, tb_file];
    for dep in dep_files {
        cmd_args.push(dep);
    }

    log_to_output(
        &output_log,
        &format!("[BUILD] 実行中: iverilog {}\n", cmd_args.join(" ")),
    );

    let output = Command::new("iverilog")
        .args(&cmd_args)
        .current_dir(directory)
        .output();

    match output {
        Ok(output) => {
            if !output.status.success() {
                log_to_output(
                    &output_log,
                    &format!(
                        "[ERROR] コンパイルエラー:\n{}\n",
                        String::from_utf8_lossy(&output.stderr)
                    ),
                );
                return;
            }
            log_to_output(&output_log, "[OK] コンパイル成功\n");
        }
        Err(e) => {
            log_to_output(
                &output_log,
                &format!("[ERROR] iverilogが見つかりません: {}\n", e),
            );
            return;
        }
    }

    // vvp実行
    log_to_output(&output_log, &format!("[RUN] 実行中: vvp {}\n", name));

    let output = Command::new("vvp")
        .arg(&name)
        .current_dir(directory)
        .output();

    match output {
        Ok(output) => {
            log_to_output(&output_log, "[OUTPUT] シミュレーション結果:\n");
            log_to_output(&output_log, &String::from_utf8_lossy(&output.stdout));
            log_to_output(&output_log, "\n");
        }
        Err(e) => {
            log_to_output(&output_log, &format!("[ERROR] vvp実行エラー: {}\n", e));
        }
    }

    // GTKWave起動
    if gtkwave_enabled {
        let vcd_file = format!("{}.vcd", name);
        let vcd_path = directory.join(&vcd_file);

        if vcd_path.exists() {
            log_to_output(&output_log, &format!("[WAVE] 実行中: gtkwave {}\n", vcd_file));

            let _ = Command::new("gtkwave")
                .arg(&vcd_file)
                .current_dir(directory)
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn();

            log_to_output(&output_log, "[OK] GTKWaveを起動しました\n");
        } else {
            log_to_output(
                &output_log,
                &format!("[WARN] VCDファイル '{}' が見つかりません\n", vcd_file),
            );
        }
    }

    // クリーンアップ
    let exec_path = directory.join(&name);
    if exec_path.exists() {
        let _ = fs::remove_file(&exec_path);
        log_to_output(&output_log, &format!("[CLEAN] 実行ファイル '{}' を削除しました\n", name));
    }

    log_to_output(
        &output_log,
        &format!("\n{}\n[完了] {} の実行完了\n{}\n\n", "=".repeat(60), name, "=".repeat(60)),
    );
}

fn log_to_output(output_log: &Arc<Mutex<String>>, message: &str) {
    let mut log = output_log.lock().unwrap();
    log.push_str(message);
}

impl eframe::App for VerilogRunnerApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading(RichText::new("Verilog HDL Runner").size(24.0));
            ui.add_space(10.0);

            // ディレクトリ選択
            ui.group(|ui| {
                ui.label(RichText::new("作業ディレクトリ").strong());
                ui.horizontal(|ui| {
                    let dir_str = self.current_dir.to_string_lossy().to_string();
                    ui.add(
                        TextEdit::singleline(&mut dir_str.clone())
                            .desired_width(800.0)
                            .interactive(false),
                    );

                    if ui.button("参照").clicked() {
                        if let Some(path) = rfd::FileDialog::new().pick_folder() {
                            self.current_dir = path;
                            self.selected_directory = self.current_dir.clone();
                            self.refresh_folder_tree();
                            self.update_testbench_list();
                        }
                    }

                    if ui.button("更新").clicked() {
                        self.refresh_folder_tree();
                        self.update_testbench_list();
                    }
                });
            });

            ui.add_space(10.0);

            // ファイル選択パネル
            ui.group(|ui| {
                ui.label(RichText::new("Verilogファイル選択").strong());
                ui.add_space(5.0);

                ui.horizontal(|ui| {
                    // 左: フォルダーツリー
                    ui.vertical(|ui| {
                        ui.set_width(350.0);
                        ui.label(RichText::new("フォルダー").strong());
                        ui.add_space(3.0);
                        
                        egui::Frame::none()
                            .inner_margin(egui::Margin::same(5.0))
                            .show(ui, |ui| {
                                ScrollArea::vertical()
                                    .max_height(400.0)
                                    .auto_shrink([false, false])
                                    .show(ui, |ui| {
                                        ui.set_width(330.0);
                                        for node in &mut self.folder_tree.clone() {
                                            self.render_folder_node(ui, node);
                                        }
                                    });
                            });
                    });

                    ui.separator();

                    // 中央: テストベンチ
                    ui.vertical(|ui| {
                        ui.set_width(350.0);
                        ui.label(RichText::new("テストベンチ (*_tb.v)").strong());
                        ui.add_space(3.0);
                        
                        egui::Frame::none()
                            .inner_margin(egui::Margin::same(5.0))
                            .show(ui, |ui| {
                                ScrollArea::vertical()
                                    .max_height(400.0)
                                    .auto_shrink([false, false])
                                    .show(ui, |ui| {
                                        ui.set_width(330.0);
                                        let tb_files = self.testbench_files.clone();
                                        for (idx, tb_file) in tb_files.iter().enumerate() {
                                            let selected = self.selected_testbench == Some(idx);
                                            if ui
                                                .selectable_label(selected, tb_file)
                                                .clicked()
                                            {
                                                self.selected_testbench = Some(idx);
                                                if self.auto_detect_enabled {
                                                    self.detect_dependencies(tb_file);
                                                } else {
                                                    self.update_dependency_list(None);
                                                }
                                            }
                                        }
                                    });
                            });
                    });

                    ui.separator();

                    // 右: 依存ファイル
                    ui.vertical(|ui| {
                        ui.set_width(350.0);
                        ui.horizontal(|ui| {
                            ui.label(RichText::new("依存ファイル").strong());
                            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                if ui.small_button("すべて選択").clicked() {
                                    self.select_all_deps();
                                }
                                if ui.small_button("すべて解除").clicked() {
                                    self.deselect_all_deps();
                                }
                            });
                        });
                        ui.add_space(3.0);

                        egui::Frame::none()
                            .inner_margin(egui::Margin::same(5.0))
                            .show(ui, |ui| {
                                ScrollArea::vertical()
                                    .max_height(400.0)
                                    .auto_shrink([false, false])
                                    .show(ui, |ui| {
                                        ui.set_width(330.0);
                                        for dep in &mut self.dependency_files {
                                            ui.checkbox(&mut dep.checked, &dep.name);
                                        }
                                    });
                            });
                    });
                });
            });

            ui.add_space(10.0);

            // オプションとボタン
            ui.horizontal(|ui| {
                ui.checkbox(&mut self.gtkwave_enabled, "GTKWaveで波形表示");
                ui.checkbox(&mut self.auto_detect_enabled, "依存ファイル自動検出");

                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    if ui.button("ログクリア").clicked() {
                        self.output_log.lock().unwrap().clear();
                    }

                    let running = *self.running.lock().unwrap();
                    ui.add_enabled_ui(!running, |ui| {
                        if ui.button(RichText::new("コンパイル & 実行").strong()).clicked() {
                            self.run_verilog();
                        }
                    });
                });
            });

            ui.add_space(10.0);

            // 実行結果
            ui.group(|ui| {
                ui.label(RichText::new("実行結果").strong());
                ScrollArea::vertical()
                    .max_height(250.0)
                    .show(ui, |ui| {
                        let log = self.output_log.lock().unwrap();
                        ui.add(
                            TextEdit::multiline(&mut log.as_str())
                                .font(egui::TextStyle::Monospace)
                                .desired_width(f32::INFINITY)
                                .interactive(false),
                        );
                    });
            });
        });

        // 定期的にUIを更新
        ctx.request_repaint();
    }
}

impl VerilogRunnerApp {
    fn render_folder_node(&mut self, ui: &mut egui::Ui, node: &mut FolderNode) {
        ui.horizontal(|ui| {
            ui.spacing_mut().item_spacing.x = 4.0;
            
            if !node.children.is_empty() {
                let arrow = if node.expanded { "▼" } else { "▶" };
                if ui.small_button(arrow).clicked() {
                    node.expanded = !node.expanded;
                }
            } else {
                ui.add_space(18.0);
            }

            let label = format!("[{}]", node.name);
            let response = ui.selectable_label(false, label);
            if response.clicked() {
                self.selected_directory = node.path.clone();
                self.update_testbench_list();
            }
        });

        if node.expanded {
            ui.indent(node.name.clone(), |ui| {
                ui.spacing_mut().indent = 16.0;
                for child in &mut node.children.clone() {
                    self.render_folder_node(ui, child);
                }
            });
        }
    }
}

impl Default for VerilogRunnerApp {
    fn default() -> Self {
        Self::new()
    }
}
