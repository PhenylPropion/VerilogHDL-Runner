import os
import subprocess
import glob
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading


class VerilogRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("🔧 Verilog HDL Runner")
        self.root.geometry("1200x750")
        
        # モダンなスタイル設定
        style = ttk.Style()
        style.theme_use('default')
        
        # カスタムカラー
        self.colors = {
            'primary': '#2563eb',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'bg_light': '#f8fafc',
            'border': '#e2e8f0'
        }
        
        # 現在のディレクトリ
        self.current_dir = os.getcwd()
        self.selected_directory = self.current_dir
        
        self._setup_ui()
        self.refresh_files()
    
    def _setup_ui(self):
        """UIコンポーネントを設定"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self._setup_directory_frame(main_frame)
        self._setup_file_frame(main_frame)
        self._setup_button_frame(main_frame)
        self._setup_output_frame(main_frame)
        self._configure_grid_weights(main_frame)
    
    def _setup_directory_frame(self, parent):
        """ディレクトリ選択フレームを設定"""
        dir_frame = ttk.LabelFrame(parent, text="📂 作業ディレクトリ", padding="10")
        dir_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.dir_var = tk.StringVar(value=self.current_dir)
        ttk.Label(dir_frame, text="ディレクトリ:", font=('', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=70, font=('', 10))
        self.dir_entry.grid(row=0, column=1, padx=(0, 5), sticky=(tk.W, tk.E))
        ttk.Button(dir_frame, text="📁 参照", command=self.browse_directory).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(dir_frame, text="🔄 更新", command=self.refresh_files).grid(row=0, column=3)
        
        dir_frame.columnconfigure(1, weight=1)
    
    def _setup_file_frame(self, parent):
        """ファイル選択フレームを設定"""
        file_frame = ttk.LabelFrame(parent, text="📝 Verilogファイル選択", padding="10")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # パネル分割器を作成
        paned = ttk.PanedWindow(file_frame, orient=tk.HORIZONTAL)
        paned.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 左側: フォルダーツリー
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=1)
        
        ttk.Label(tree_frame, text="📁 フォルダー", font=('', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        tree_scroll_frame = ttk.Frame(tree_frame)
        tree_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.folder_tree = ttk.Treeview(tree_scroll_frame, selectmode="browse")
        tree_scrollbar = ttk.Scrollbar(tree_scroll_frame, orient="vertical", command=self.folder_tree.yview)
        self.folder_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.folder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.folder_tree.bind("<<TreeviewSelect>>", self.on_folder_select)
        
        # 中央: テストベンチファイルリスト
        tb_list_frame = ttk.Frame(paned)
        paned.add(tb_list_frame, weight=1)
        
        ttk.Label(tb_list_frame, text="🧪 テストベンチ (*_tb.v)", font=('', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        tb_scroll_frame = ttk.Frame(tb_list_frame)
        tb_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tb_listbox = tk.Listbox(tb_scroll_frame, height=10, selectmode=tk.SINGLE, 
                                      bg='#f0f8ff', font=('', 10), relief=tk.FLAT, 
                                      borderwidth=1, highlightthickness=1, highlightcolor=self.colors['primary'])
        tb_scrollbar = ttk.Scrollbar(tb_scroll_frame, orient="vertical", command=self.tb_listbox.yview)
        self.tb_listbox.configure(yscrollcommand=tb_scrollbar.set)
        
        self.tb_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tb_listbox.bind("<<ListboxSelect>>", self.on_testbench_select)
        
        # 右側: 依存ファイルリスト
        dep_list_frame = ttk.Frame(paned)
        paned.add(dep_list_frame, weight=1)
        
        dep_header = ttk.Frame(dep_list_frame)
        dep_header.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(dep_header, text="📄 依存ファイル", font=('', 11, 'bold')).pack(side=tk.LEFT)
        ttk.Button(dep_header, text="すべて選択", command=self.select_all_deps, width=12).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(dep_header, text="すべて解除", command=self.deselect_all_deps, width=12).pack(side=tk.RIGHT)
        
        # Checkbuttonを使ったリスト
        dep_canvas_frame = ttk.Frame(dep_list_frame)
        dep_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.dep_canvas = tk.Canvas(dep_canvas_frame, bg='white', highlightthickness=1, 
                                    highlightbackground=self.colors['border'])
        dep_scrollbar = ttk.Scrollbar(dep_canvas_frame, orient="vertical", command=self.dep_canvas.yview)
        self.dep_checkbutton_frame = ttk.Frame(self.dep_canvas)
        
        self.dep_checkbutton_frame.bind(
            "<Configure>",
            lambda e: self.dep_canvas.configure(scrollregion=self.dep_canvas.bbox("all"))
        )
        
        self.dep_canvas.create_window((0, 0), window=self.dep_checkbutton_frame, anchor="nw")
        self.dep_canvas.configure(yscrollcommand=dep_scrollbar.set)
        
        self.dep_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dep_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dep_vars = []
        self.dep_files = []
        
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(0, weight=1)
    
    def _setup_button_frame(self, parent):
        """ボタンフレームを設定"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # 左側のオプション
        left_options = ttk.Frame(button_frame)
        left_options.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.gtkwave_var = tk.BooleanVar(value=True)
        self.gtkwave_checkbox = ttk.Checkbutton(
            left_options, 
            text="📊 GTKWaveで波形表示", 
            variable=self.gtkwave_var
        )
        self.gtkwave_checkbox.pack(side=tk.LEFT, padx=(0, 20))
        
        self.auto_detect_var = tk.BooleanVar(value=True)
        self.auto_detect_checkbox = ttk.Checkbutton(
            left_options,
            text="🔍 依存ファイル自動検出",
            variable=self.auto_detect_var,
            command=self.on_auto_detect_toggle
        )
        self.auto_detect_checkbox.pack(side=tk.LEFT)
        
        # 右側のボタン
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        self.run_button = ttk.Button(right_buttons, text="▶️ コンパイル & 実行", 
                                      command=self.run_verilog)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(right_buttons, text="🗑️ ログクリア", 
                                        command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT)
    
    def _setup_output_frame(self, parent):
        """出力フレームを設定"""
        output_frame = ttk.LabelFrame(parent, text="📋 実行結果", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, height=18, width=100, 
            font=('Menlo', 10), bg='#1e1e1e', fg='#d4d4d4',
            insertbackground='white', relief=tk.FLAT, padx=10, pady=10
        )
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # カラータグを設定
        self.output_text.tag_config('success', foreground='#4ade80')
        self.output_text.tag_config('error', foreground='#f87171')
        self.output_text.tag_config('warning', foreground='#fbbf24')
        self.output_text.tag_config('info', foreground='#60a5fa')
        self.output_text.tag_config('header', foreground='#a78bfa', font=('Menlo', 10, 'bold'))
        
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
    
    def _configure_grid_weights(self, main_frame):
        """グリッドの重み設定"""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=2)
        main_frame.rowconfigure(3, weight=1)
    
    def browse_directory(self):
        """ディレクトリ選択ダイアログ"""
        directory = filedialog.askdirectory(initialdir=self.current_dir)
        if directory:
            self.current_dir = directory
            self.dir_var.set(directory)
            self.refresh_files()
    
    def refresh_files(self):
        """フォルダーツリーとVerilogファイルリストを更新"""
        try:
            directory = self.dir_var.get()
            if not os.path.exists(directory):
                self.log_output("エラー: 指定されたディレクトリが存在しません。\n", 'error')
                return
            
            os.chdir(directory)
            self.current_dir = directory
            
            self.populate_folder_tree(directory)
            self.update_file_list(directory)
            
            self.log_output(f"✓ ディレクトリを更新: {directory}\n\n", 'success')
            
        except Exception as e:
            self.log_output(f"エラー: {e}\n", 'error')
    
    def populate_folder_tree(self, root_dir):
        """フォルダーツリーを構築"""
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
        
        root_name = os.path.basename(root_dir) or root_dir
        root_item = self.folder_tree.insert("", "end", text=f"📁 {root_name}", values=[root_dir], open=True)
        
        self.add_directories_to_tree(root_item, root_dir)
    
    def add_directories_to_tree(self, parent_item, parent_dir):
        """ツリーにディレクトリを再帰的に追加"""
        try:
            items = []
            for item in os.listdir(parent_dir):
                item_path = os.path.join(parent_dir, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    if self.has_verilog_files(item_path):
                        items.append((item, item_path))
            
            for item_name, item_path in sorted(items):
                child_item = self.folder_tree.insert(parent_item, "end", text=f"📁 {item_name}", values=[item_path])
                self.add_directories_to_tree(child_item, item_path)
                
        except PermissionError:
            pass
    
    def has_verilog_files(self, directory):
        """ディレクトリ内にVerilogファイルがあるかチェック"""
        try:
            verilog_files = glob.glob(os.path.join(directory, "*.v"))
            if verilog_files:
                return True
            
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    if self.has_verilog_files(item_path):
                        return True
            return False
        except (PermissionError, OSError):
            return False
    
    def on_folder_select(self, event):
        """フォルダー選択時のイベントハンドラ"""
        selection = self.folder_tree.selection()
        if selection:
            item = selection[0]
            folder_path = self.folder_tree.item(item, "values")[0]
            self.update_file_list(folder_path)
    
    def update_file_list(self, directory):
        """指定ディレクトリのテストベンチファイルリストを更新"""
        try:
            self.tb_listbox.delete(0, tk.END)
            self.selected_directory = directory
            
            # テストベンチファイルを検索
            pattern = os.path.join(directory, "*_tb.v")
            tb_files = glob.glob(pattern)
            
            for file_path in sorted(tb_files):
                file_name = os.path.basename(file_path)
                display_text = f"🧪 {file_name}"
                self.tb_listbox.insert(tk.END, display_text)
            
            # 依存ファイルリストをクリア
            self.clear_dependency_list()
            
        except Exception as e:
            self.log_output(f"ファイルリスト更新エラー: {e}\n", 'error')
    
    def on_testbench_select(self, event):
        """テストベンチ選択時のイベントハンドラ"""
        selection = self.tb_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.tb_listbox.get(selection[0])
        tb_file = selected_text.replace('🧪 ', '')
        
        if self.auto_detect_var.get():
            self.detect_dependencies(tb_file)
        else:
            self.update_dependency_list(tb_file)
    
    def detect_dependencies(self, tb_file):
        """テストベンチファイルから依存ファイルを自動検出"""
        tb_path = os.path.join(self.selected_directory, tb_file)
        dependencies = set()
        
        try:
            with open(tb_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Verilog予約語リスト
            reserved_words = {
                'module', 'endmodule', 'initial', 'always', 'assign', 'wire', 'reg', 
                'integer', 'input', 'output', 'inout', 'parameter', 'localparam',
                'begin', 'end', 'if', 'else', 'case', 'casex', 'casez', 'default',
                'for', 'while', 'repeat', 'forever', 'task', 'function', 'and', 'or',
                'not', 'nand', 'nor', 'xor', 'xnor', 'buf', 'bufif0', 'bufif1',
                'notif0', 'notif1', 'posedge', 'negedge'
            }
            
            # モジュールインスタンス化を検索（より柔軟なパターン）
            # パターン: モジュール名 インスタンス名 (
            module_pattern = r'^\s*(\w+)\s+(\w+)\s*\('
            matches = re.finditer(module_pattern, content, re.MULTILINE)
            
            for match in matches:
                module_name = match.group(1)
                # 予約語を除外
                if module_name.lower() not in reserved_words:
                    module_file = f"{module_name}.v"
                    module_path = os.path.join(self.selected_directory, module_file)
                    if os.path.exists(module_path):
                        dependencies.add(module_file)
            
            # メインモジュールファイルを追加（テストベンチと同じ名前から_tbを除いたもの）
            main_module = tb_file.replace('_tb.v', '.v')
            main_path = os.path.join(self.selected_directory, main_module)
            if os.path.exists(main_path):
                dependencies.add(main_module)
            
            # add1.vの依存関係を再帰的に検出
            self.detect_nested_dependencies(dependencies, self.selected_directory)
            
            self.update_dependency_list(tb_file, list(dependencies))
            
        except Exception as e:
            self.log_output(f"依存ファイル検出エラー: {e}\n", 'error')
            self.update_dependency_list(tb_file)
    
    def detect_nested_dependencies(self, dependencies, directory):
        """依存ファイルの中からさらに依存ファイルを再帰的に検出"""
        # Verilog予約語リスト
        reserved_words = {
            'module', 'endmodule', 'initial', 'always', 'assign', 'wire', 'reg', 
            'integer', 'input', 'output', 'inout', 'parameter', 'localparam',
            'begin', 'end', 'if', 'else', 'case', 'casex', 'casez', 'default',
            'for', 'while', 'repeat', 'forever', 'task', 'function', 'and', 'or',
            'not', 'nand', 'nor', 'xor', 'xnor', 'buf', 'bufif0', 'bufif1',
            'notif0', 'notif1', 'posedge', 'negedge'
        }
        
        files_to_check = list(dependencies)
        checked_files = set()
        
        while files_to_check:
            current_file = files_to_check.pop(0)
            if current_file in checked_files:
                continue
            checked_files.add(current_file)
            
            file_path = os.path.join(directory, current_file)
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # モジュールインスタンス化を検索
                module_pattern = r'^\s*(\w+)\s+(\w+)\s*\('
                matches = re.finditer(module_pattern, content, re.MULTILINE)
                
                for match in matches:
                    module_name = match.group(1)
                    if module_name.lower() not in reserved_words:
                        module_file = f"{module_name}.v"
                        module_path = os.path.join(directory, module_file)
                        if os.path.exists(module_path) and module_file not in dependencies:
                            dependencies.add(module_file)
                            files_to_check.append(module_file)
            except Exception:
                pass
    
    def update_dependency_list(self, tb_file, auto_detected=None):
        """依存ファイルリストを更新"""
        self.clear_dependency_list()
        
        # 全てのVerilogファイルを取得（テストベンチを除く）
        pattern = os.path.join(self.selected_directory, "*.v")
        all_files = [os.path.basename(f) for f in glob.glob(pattern) 
                     if not f.endswith('_tb.v')]
        
        for file_name in sorted(all_files):
            var = tk.BooleanVar()
            
            # 自動検出されたファイルはチェック
            if auto_detected and file_name in auto_detected:
                var.set(True)
            
            cb = ttk.Checkbutton(
                self.dep_checkbutton_frame,
                text=f"  📄 {file_name}",
                variable=var,
                onvalue=True,
                offvalue=False
            )
            cb.pack(anchor=tk.W, padx=5, pady=2)
            
            self.dep_vars.append(var)
            self.dep_files.append(file_name)
    
    def clear_dependency_list(self):
        """依存ファイルリストをクリア"""
        for widget in self.dep_checkbutton_frame.winfo_children():
            widget.destroy()
        self.dep_vars.clear()
        self.dep_files.clear()
    
    def select_all_deps(self):
        """すべての依存ファイルを選択"""
        for var in self.dep_vars:
            var.set(True)
    
    def deselect_all_deps(self):
        """すべての依存ファイルを解除"""
        for var in self.dep_vars:
            var.set(False)
    
    def on_auto_detect_toggle(self):
        """自動検出トグル時の処理"""
        selection = self.tb_listbox.curselection()
        if selection:
            self.on_testbench_select(None)
    
    def get_selected_files(self):
        """選択されたテストベンチと依存ファイルを取得"""
        tb_selection = self.tb_listbox.curselection()
        if not tb_selection:
            return None, None, None
        
        selected_text = self.tb_listbox.get(tb_selection[0])
        tb_file = selected_text.replace('🧪 ', '')
        
        # 選択された依存ファイルを取得
        dep_files = [self.dep_files[i] for i, var in enumerate(self.dep_vars) if var.get()]
        
        return tb_file, dep_files, self.selected_directory
    
    def run_iverilog(self, name, tb_file, dep_files, directory):
        """iverilogコマンドを実行（複数ファイル対応）"""
        cmd = ["iverilog", "-Wall", "-o", name, tb_file] + dep_files
        self.log_output(f"🔨 実行中: {' '.join(cmd)}\n", 'info')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=directory)
            if result.returncode != 0:
                self.log_output(f"❌ コンパイルエラー:\n{result.stderr}\n", 'error')
                return False
            
            self.log_output(f"✓ コンパイル成功\n", 'success')
            if result.stdout:
                self.log_output(f"{result.stdout}\n")
            return True
            
        except FileNotFoundError:
            self.log_output("❌ エラー: iverilogが見つかりません。Icarus Verilogがインストールされているか確認してください。\n", 'error')
            return False
    
    def run_vvp(self, name, directory):
        """vvpコマンドを実行"""
        cmd = ["vvp", name]
        self.log_output(f"⚡ 実行中: {' '.join(cmd)}\n", 'info')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=directory)
            self.log_output("📊 シミュレーション結果:\n", 'header')
            self.log_output(f"{result.stdout}\n")
            if result.stderr:
                self.log_output(f"⚠️  警告:\n{result.stderr}\n", 'warning')
            return result.returncode == 0
        except FileNotFoundError:
            self.log_output("❌ エラー: vvpが見つかりません。\n", 'error')
            return False
    
    def cleanup_file(self, name, directory):
        """生成された実行ファイルを削除"""
        filepath = os.path.join(directory, name)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                self.log_output(f"🗑️  実行ファイル '{name}' を削除しました。\n", 'info')
            except OSError as e:
                self.log_output(f"ファイル削除エラー: {e}\n", 'error')
    
    def run_gtkwave(self, name, directory):
        """gtkwaveコマンドを実行して波形を表示"""
        vcd_file = os.path.join(directory, f"{name}.vcd")
        
        if not os.path.exists(vcd_file):
            self.log_output(f"⚠️  警告: VCDファイル '{name}.vcd' が見つかりません。\n", 'warning')
            return False
        
        cmd = ["gtkwave", f"{name}.vcd"]
        self.log_output(f"📈 実行中: {' '.join(cmd)}\n", 'info')
        
        try:
            process = subprocess.Popen(
                cmd, 
                cwd=directory,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.log_output(f"✓ GTKWaveを起動しました (PID: {process.pid})\n", 'success')
            return True
        except FileNotFoundError:
            self.log_output("❌ エラー: gtkwaveが見つかりません。\n", 'error')
            return False
        except OSError as e:
            self.log_output(f"GTKWave起動エラー: {e}\n", 'error')
            return False
    
    def log_output(self, text, tag=None):
        """出力エリアにテキストを追加"""
        self.output_text.insert(tk.END, text, tag)
        self.output_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """ログをクリア"""
        self.output_text.delete(1.0, tk.END)
    
    def run_verilog_thread(self, tb_file, dep_files, directory):
        """Verilogコンパイル・実行をバックグラウンドで実行"""
        try:
            # 実行ファイル名（.vを除く）
            name = tb_file.replace('_tb.v', '')
            
            self.log_output(f"\n{'='*60}\n", 'header')
            self.log_output(f"🚀 {name} の実行を開始\n", 'header')
            self.log_output(f"{'='*60}\n\n", 'header')
            self.log_output(f"📂 作業ディレクトリ: {directory}\n", 'info')
            self.log_output(f"🧪 テストベンチ: {tb_file}\n", 'info')
            self.log_output(f"📄 依存ファイル: {', '.join(dep_files) if dep_files else 'なし'}\n\n", 'info')
            
            if (self.run_iverilog(name, tb_file, dep_files, directory) and 
                self.run_vvp(name, directory)):
                
                if self.gtkwave_var.get():
                    self.run_gtkwave(name, directory)
            
            self.cleanup_file(name, directory)
            
            self.log_output(f"\n{'='*60}\n", 'header')
            self.log_output(f"✅ {name} の実行完了\n", 'success')
            self.log_output(f"{'='*60}\n\n", 'header')
            
        except Exception as e:
            self.log_output(f"❌ 予期しないエラー: {e}\n", 'error')
        finally:
            self.root.after(0, lambda: self.run_button.config(state="normal"))
    
    def run_verilog(self):
        """Verilogファイルを実行"""
        file_info = self.get_selected_files()
        if not file_info or not file_info[0]:
            messagebox.showwarning("警告", "テストベンチファイルを選択してください。")
            return
        
        tb_file, dep_files, directory = file_info
        
        if not dep_files:
            response = messagebox.askyesno(
                "確認", 
                "依存ファイルが選択されていません。\nテストベンチファイルのみで実行しますか?"
            )
            if not response:
                return
        
        self.run_button.config(state="disabled")
        
        thread = threading.Thread(
            target=self.run_verilog_thread, 
            args=(tb_file, dep_files, directory), 
            daemon=True
        )
        thread.start()


def main():
    root = tk.Tk()
    app = VerilogRunner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
