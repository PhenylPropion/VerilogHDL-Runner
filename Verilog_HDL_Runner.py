import os
import subprocess
import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading


class VerilogRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("Verilog HDL Runner")
        self.root.geometry("1000x700")  # 幅を広げる
        
        # 現在のディレクトリ
        self.current_dir = os.getcwd()
        self.selected_directory = self.current_dir  # 現在選択されているディレクトリ
        
        self._setup_ui()
        self.refresh_files()
    
    def _setup_ui(self):
        """UIコンポーネントを設定"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self._setup_directory_frame(main_frame)
        self._setup_file_frame(main_frame)
        self._setup_button_frame(main_frame)
        self._setup_output_frame(main_frame)
        self._configure_grid_weights(main_frame)
    
    def _setup_directory_frame(self, parent):
        """ディレクトリ選択フレームを設定"""
        dir_frame = ttk.LabelFrame(parent, text="作業ディレクトリ", padding="5")
        dir_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.dir_var = tk.StringVar(value=self.current_dir)
        ttk.Label(dir_frame, text="ディレクトリ:").grid(row=0, column=0, sticky=tk.W)
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=60)
        self.dir_entry.grid(row=0, column=1, padx=(5, 5), sticky=(tk.W, tk.E))
        ttk.Button(dir_frame, text="参照", command=self.browse_directory).grid(row=0, column=2)
        ttk.Button(dir_frame, text="更新", command=self.refresh_files).grid(row=0, column=3, padx=(5, 0))
        
        dir_frame.columnconfigure(1, weight=1)
    
    def _setup_file_frame(self, parent):
        """ファイル選択フレームを設定"""
        file_frame = ttk.LabelFrame(parent, text="Verilogファイル選択", padding="5")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # パネル分割器を作成
        paned = ttk.PanedWindow(file_frame, orient=tk.HORIZONTAL)
        paned.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 左側：フォルダーツリー
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=1)
        
        ttk.Label(tree_frame, text="フォルダー").pack(anchor=tk.W)
        self.folder_tree = ttk.Treeview(tree_frame, selectmode="browse")
        self.folder_tree.pack(fill=tk.BOTH, expand=True, padx=(0, 5))
        self.folder_tree.bind("<<TreeviewSelect>>", self.on_folder_select)
        
        # ツリービューのスクロールバー
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.folder_tree.yview)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.folder_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # 右側：ファイルリスト
        file_list_frame = ttk.Frame(paned)
        paned.add(file_list_frame, weight=1)
        
        ttk.Label(file_list_frame, text="Verilogファイル").pack(anchor=tk.W)
        self.file_listbox = tk.Listbox(file_list_frame, height=8)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # ファイルリストのスクロールバー
        file_scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=self.file_listbox.yview)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.configure(yscrollcommand=file_scrollbar.set)
        
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(0, weight=1)
    
    def _setup_button_frame(self, parent):
        """ボタンフレームを設定"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # GTKWaveチェックボックス
        self.gtkwave_var = tk.BooleanVar(value=True)
        self.gtkwave_checkbox = ttk.Checkbutton(
            button_frame, 
            text="GTKWaveで波形表示", 
            variable=self.gtkwave_var
        )
        self.gtkwave_checkbox.pack(side=tk.LEFT, padx=(0, 10))
        
        self.run_button = ttk.Button(button_frame, text="コンパイル & 実行", command=self.run_verilog)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="ログクリア", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT)
    
    def _setup_output_frame(self, parent):
        """出力フレームを設定"""
        output_frame = ttk.LabelFrame(parent, text="実行結果", padding="5")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
    
    def _configure_grid_weights(self, main_frame):
        """グリッドの重み設定"""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
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
                self.log_output("エラー: 指定されたディレクトリが存在しません。\n")
                return
            
            # ディレクトリを変更
            os.chdir(directory)
            self.current_dir = directory
            
            # フォルダーツリーを更新
            self.populate_folder_tree(directory)
            
            # カレントディレクトリのVerilogファイルを表示
            self.update_file_list(directory)
            
            self.log_output(f"ディレクトリを更新: {directory}\n\n")
            
        except Exception as e:
            self.log_output(f"エラー: {e}\n")
    
    def populate_folder_tree(self, root_dir):
        """フォルダーツリーを構築"""
        # ツリーをクリア
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
        
        # ルートディレクトリを追加
        root_name = os.path.basename(root_dir) or root_dir
        root_item = self.folder_tree.insert("", "end", text=root_name, values=[root_dir], open=True)
        
        # サブディレクトリを再帰的に追加
        self.add_directories_to_tree(root_item, root_dir)
    
    def add_directories_to_tree(self, parent_item, parent_dir):
        """ツリーにディレクトリを再帰的に追加"""
        try:
            items = []
            for item in os.listdir(parent_dir):
                item_path = os.path.join(parent_dir, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    # Verilogファイルがあるかチェック
                    has_verilog = self.has_verilog_files(item_path)
                    if has_verilog:
                        items.append((item, item_path))
            
            # ソートして追加
            for item_name, item_path in sorted(items):
                child_item = self.folder_tree.insert(parent_item, "end", text=item_name, values=[item_path])
                # 再帰的にサブディレクトリを追加
                self.add_directories_to_tree(child_item, item_path)
                
        except PermissionError:
            pass  # アクセス権限がない場合はスキップ
    
    def has_verilog_files(self, directory):
        """ディレクトリ内にVerilogファイルがあるかチェック（再帰的）"""
        try:
            # 直接のVerilogファイル
            verilog_files = glob.glob(os.path.join(directory, "*.v"))
            if any(not f.endswith('_tb.v') for f in verilog_files):
                return True
            
            # サブディレクトリもチェック
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
        """指定ディレクトリのVerilogファイルリストを更新"""
        try:
            # ファイルリストをクリア
            self.file_listbox.delete(0, tk.END)
            
            # Verilogファイルを検索（テストベンチファイルを除外）
            pattern = os.path.join(directory, "*.v")
            verilog_files = [f for f in glob.glob(pattern) if not f.endswith('_tb.v')]
            
            # ファイル名のみを表示（拡張子なし）
            for file_path in sorted(verilog_files):
                file_name = os.path.basename(file_path)[:-2]  # .v拡張子を除去
                display_text = f"{file_name} ({os.path.relpath(file_path, self.current_dir)})"
                self.file_listbox.insert(tk.END, display_text)
                # ファイルの完全パスを保存（後で使用）
                self.file_listbox.insert(tk.END, "")  # プレースホルダー
                self.file_listbox.delete(tk.END)  # 削除してデータを保存
            
            # 選択されたディレクトリを記録
            self.selected_directory = directory
            
        except Exception as e:
            self.log_output(f"ファイルリスト更新エラー: {e}\n")
    
    def get_selected_file(self):
        """選択されたファイル名を取得"""
        selection = self.file_listbox.curselection()
        if not selection:
            return None, None
        
        selected_text = self.file_listbox.get(selection[0])
        # ファイル名を抽出（括弧の前の部分）
        file_name = selected_text.split(' (')[0]
        
        return file_name, self.selected_directory
    
    def check_files_exist(self, name, directory):
        """必要なファイルが存在するかチェック"""
        files = {
            'testbench': os.path.join(directory, f"{name}_tb.v"),
            'main': os.path.join(directory, f"{name}.v")
        }
        
        for file_type, filepath in files.items():
            if not os.path.exists(filepath):
                self.log_output(f"エラー: {file_type}ファイル '{filepath}' が見つかりません。\n")
                return False
        return True
    
    def _run_command(self, cmd, success_msg, error_prefix, cwd=None):
        """共通のコマンド実行処理"""
        self.log_output(f"実行中: {' '.join(cmd)}\n")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or self.current_dir)
            if result.returncode != 0:
                self.log_output(f"{error_prefix}:\n{result.stderr}\n")
                return False
            
            self.log_output(f"{success_msg}\n")
            if result.stdout:
                self.log_output(f"{result.stdout}\n")
            return True
            
        except FileNotFoundError:
            tool_name = cmd[0]
            self.log_output(f"エラー: {tool_name}が見つかりません。{tool_name}がインストールされているか確認してください。\n")
            return False
    
    def run_iverilog(self, name, directory):
        """iverilogコマンドを実行"""
        cmd = ["iverilog", "-Wall", "-o", name, f"{name}_tb.v", f"{name}.v"]
        return self._run_command(cmd, "コンパイル成功", "iverilogエラー", directory)
    
    def run_vvp(self, name, directory):
        """vvpコマンドを実行"""
        cmd = ["vvp", name]
        self.log_output(f"実行中: {' '.join(cmd)}\n")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=directory)
            self.log_output("シミュレーション結果:\n")
            self.log_output(f"{result.stdout}\n")
            if result.stderr:
                self.log_output(f"エラー出力:\n{result.stderr}\n")
            return result.returncode == 0
        except FileNotFoundError:
            self.log_output("エラー: vvpが見つかりません。Icarus Verilogがインストールされているか確認してください。\n")
            return False
    
    def cleanup_file(self, name, directory):
        """生成された実行ファイルを削除"""
        filepath = os.path.join(directory, name)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                self.log_output(f"実行ファイル '{name}' を削除しました。\n")
            except OSError as e:
                self.log_output(f"ファイル削除エラー: {e}\n")
    
    def run_gtkwave(self, name, directory):
        """gtkwaveコマンドを実行して波形を表示"""
        vcd_file = os.path.join(directory, f"{name}.vcd")
        
        if not os.path.exists(vcd_file):
            self.log_output(f"警告: VCDファイル '{name}.vcd' が見つかりません。波形表示をスキップします。\n")
            return False
        
        cmd = ["gtkwave", f"{name}.vcd"]
        self.log_output(f"実行中: {' '.join(cmd)}\n")
        
        try:
            process = subprocess.Popen(
                cmd, 
                cwd=directory,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.log_output(f"GTKWaveを起動しました (PID: {process.pid})\n")
            return True
        except FileNotFoundError:
            self.log_output("エラー: gtkwaveが見つかりません。GTKWaveがインストールされているか確認してください。\n")
            return False
        except OSError as e:
            self.log_output(f"GTKWave起動エラー: {e}\n")
            return False
    
    def log_output(self, text):
        """出力エリアにテキストを追加"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """ログをクリア"""
        self.output_text.delete(1.0, tk.END)
    
    def run_verilog_thread(self, name, directory):
        """Verilogコンパイル・実行をバックグラウンドで実行"""
        try:
            self.log_output(f"=== {name} の実行を開始 ({directory}) ===\n")
            
            # ファイル存在確認 → コンパイル → 実行 → 波形表示 → クリーンアップ
            if (self.check_files_exist(name, directory) and 
                self.run_iverilog(name, directory) and 
                self.run_vvp(name, directory)):
                
                if self.gtkwave_var.get():
                    self.run_gtkwave(name, directory)
            
            self.cleanup_file(name, directory)
            self.log_output(f"=== {name} の実行完了 ===\n\n")
            
        except Exception as e:
            self.log_output(f"予期しないエラー: {e}\n")
        finally:
            # ボタンを再有効化
            self.root.after(0, lambda: self.run_button.config(state="normal"))
    
    def run_verilog(self):
        """Verilogファイルを実行"""
        file_info = self.get_selected_file()
        if not file_info or not file_info[0]:
            messagebox.showwarning("警告", "Verilogファイルを選択してください。")
            return
        
        selected_file, selected_directory = file_info
        
        # ボタンを無効化
        self.run_button.config(state="disabled")
        
        # バックグラウンドで実行
        thread = threading.Thread(
            target=self.run_verilog_thread, 
            args=(selected_file, selected_directory), 
            daemon=True
        )
        thread.start()


def main():
    root = tk.Tk()
    app = VerilogRunner(root)
    root.mainloop()


if __name__ == "__main__":
    main()