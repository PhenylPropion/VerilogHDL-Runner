# Verilog HDL Runner - クイックスタートガイド

## 🚀 インストール方法

### macOS

#### 方法1: アプリケーションバンドル（推奨）

1. `verilog-hdl-runner-dist.zip` をダウンロード
2. ZIPファイルを解凍
3. `Verilog HDL Runner.app` を **Applicationsフォルダ** にドラッグ&ドロップ
4. Launchpadまたは Applicationsフォルダから起動

#### 方法2: コマンドラインツール

```bash
# ZIPを解凍
unzip verilog-hdl-runner-dist.zip
cd verilog-hdl-runner-dist

# インストールスクリプトを実行
./install.sh

# 以下を ~/.zshrc に追加
export PATH="$HOME/.local/bin:$PATH"

# シェルを再起動
source ~/.zshrc

# 実行
verilog-hdl-runner
```

### Linux

```bash
# ZIPを解凍
unzip verilog-hdl-runner-dist.zip
cd verilog-hdl-runner-dist

# インストール
./install.sh

# PATHに追加（~/.bashrc または ~/.zshrc）
export PATH="$HOME/.local/bin:$PATH"

# シェルを再起動
source ~/.bashrc  # または source ~/.zshrc

# 実行
verilog-hdl-runner
```

### Windows

1. `verilog-hdl-runner.exe` をダウンロード
2. 任意のフォルダに配置
3. ダブルクリックで起動

## 📋 必要要件

### 必須

**Icarus Verilog** (iverilog, vvp)

```bash
# macOS
brew install icarus-verilog

# Ubuntu/Debian
sudo apt install iverilog

# Windows
# http://bleyer.org/icarus/ からインストーラーをダウンロード
```

### オプション（波形表示用）

**GTKWave**

```bash
# macOS
brew install gtkwave

# Ubuntu/Debian  
sudo apt install gtkwave

# Windows
# http://gtkwave.sourceforge.net/ からダウンロード
```

## 🎯 基本的な使い方

### 1. プロジェクトを開く

1. アプリケーションを起動
2. 「参照」ボタンをクリック
3. Verilogプロジェクトのルートディレクトリを選択

### 2. テストベンチを選択

1. **左側**: フォルダーツリーから対象フォルダーをクリック
2. **中央**: テストベンチファイル（`*_tb.v`）を選択
3. **右側**: 依存ファイルが自動的に選択される

### 3. 実行

1. 「コンパイル & 実行」ボタンをクリック
2. 下部のログエリアで実行結果を確認
3. GTKWaveが自動的に起動（有効な場合）

## 📁 プロジェクト構造の例

```
my_verilog_project/
├── alu8.v              # メインモジュール
├── alu8_tb.v          # テストベンチ
├── half_adder.v       # 依存モジュール
└── full_adder.v       # 依存モジュール
```

このような構造の場合:
1. `my_verilog_project` フォルダーを開く
2. `alu8_tb.v` を選択
3. 依存ファイル（`alu8.v`, `half_adder.v`, `full_adder.v`）が自動検出される

## ⚙️ 機能

### 自動依存検出

テストベンチファイルを解析し、以下を自動検出:
- モジュールのインスタンス化
- 必要なソースファイル
- 階層的な依存関係

手動で調整することも可能です。

### 複数ファイルコンパイル

以下のようなコマンドを自動生成:

```bash
iverilog -Wall -o alu8 alu8_tb.v alu8.v half_adder.v full_adder.v
vvp alu8
gtkwave alu8.vcd &
```

### リアルタイムログ

コンパイル、実行、エラーメッセージをリアルタイムで表示:
- `[BUILD]` コンパイル状況
- `[OK]` 成功メッセージ
- `[ERROR]` エラー詳細
- `[OUTPUT]` シミュレーション結果

## 🔧 設定オプション

### GTKWave自動起動

チェックボックスで切り替え:
- ✅ 有効: 実行後に自動的にGTKWaveで波形表示
- ❌ 無効: VCDファイルのみ生成

### 依存ファイル自動検出

チェックボックスで切り替え:
- ✅ 有効: テストベンチ選択時に自動検出
- ❌ 無効: 手動で選択

## 🐛 トラブルシューティング

### "iverilogが見つかりません"

```bash
# インストールされているか確認
which iverilog

# PATHを確認
echo $PATH

# Homebrewでインストールした場合（macOS）
export PATH="/opt/homebrew/bin:$PATH"  # Apple Silicon
export PATH="/usr/local/bin:$PATH"      # Intel Mac
```

### "アプリケーションを開けません"（macOS）

```bash
# セキュリティ設定を確認
xattr -d com.apple.quarantine "Verilog HDL Runner.app"

# または
chmod +x verilog-hdl-runner
```

### フォルダーが表示されない

- `.v` ファイルが含まれるフォルダーのみ表示されます
- 隠しフォルダー（`.`で始まる）は表示されません

### 依存ファイルが自動検出されない

手動で選択できます:
1. 右側の依存ファイルリストでチェックボックスを使用
2. 「すべて選択」ボタンで一括選択

## 📊 対応フォーマット

### テストベンチファイル

ファイル名が `*_tb.v` で終わるVerilogファイル

例:
- `alu_tb.v`
- `adder_tb.v`
- `my_module_tb.v`

### 依存ファイル

`.v` 拡張子のVerilogファイル（テストベンチを除く）

## 🎓 使用例

### 例1: シンプルなAND回路

```verilog
// and_gate.v
module and_gate(input a, b, output y);
    assign y = a & b;
endmodule

// and_gate_tb.v
module and_gate_tb;
    reg a, b;
    wire y;
    
    and_gate dut(a, b, y);
    
    initial begin
        $dumpfile("and_gate.vcd");
        $dumpvars(0, and_gate_tb);
        
        a = 0; b = 0; #10;
        a = 0; b = 1; #10;
        a = 1; b = 0; #10;
        a = 1; b = 1; #10;
        
        $finish;
    end
endmodule
```

### 例2: 複数モジュール

```verilog
// half_adder.v
module half_adder(input a, b, output sum, carry);
    assign sum = a ^ b;
    assign carry = a & b;
endmodule

// full_adder.v
module full_adder(input a, b, cin, output sum, cout);
    wire s1, c1, c2;
    half_adder ha1(a, b, s1, c1);
    half_adder ha2(s1, cin, sum, c2);
    assign cout = c1 | c2;
endmodule

// full_adder_tb.v
module full_adder_tb;
    // テストコード
endmodule
```

このアプリで:
1. `full_adder_tb.v` を選択
2. `full_adder.v` と `half_adder.v` が自動検出される
3. ワンクリックで実行

## 💡 ヒント

- **ショートカット**: プロジェクトをよく使う場所に配置
- **ログの保存**: ログエリアから選択してコピー可能
- **複数プロジェクト**: 「参照」ボタンで簡単に切り替え
- **エラー確認**: コンパイルエラーは `[ERROR]` セクションに表示

## 📞 サポート

問題が発生した場合:
1. このドキュメントのトラブルシューティングを確認
2. `DISTRIBUTION.md` で詳細な配布ガイドを確認
3. GitHub Issuesで報告

## 📄 ライセンス

MIT License - 自由に使用・配布可能
