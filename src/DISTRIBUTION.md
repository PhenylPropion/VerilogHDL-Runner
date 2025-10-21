# Verilog HDL Runner - 配布ガイド

## 📦 配布パッケージの作成

### macOS/Linux での配布パッケージ作成

```bash
# 1. 配布パッケージをビルド
./build_dist.sh

# 生成物:
# - verilog-hdl-runner-dist/ (配布ディレクトリ)
# - verilog-hdl-runner-dist.zip (配布用ZIP)
# - Verilog HDL Runner.app (macOSアプリ、macOSのみ)
```

### Windows向けビルド（macOS/Linuxから）

```bash
# Windows向けのクロスコンパイルターゲットを追加
rustup target add x86_64-pc-windows-gnu

# Windowsリンカーをインストール（macOS）
brew install mingw-w64

# ビルド
cargo build --release --target x86_64-pc-windows-gnu

# 生成物: target/x86_64-pc-windows-gnu/release/verilog-hdl-runner.exe
```

## 📤 配布方法

### 方法1: ZIPファイルで配布

1. `build_dist.sh` を実行
2. 生成された `verilog-hdl-runner-dist.zip` を配布
3. 受信者は以下の手順でインストール:
   ```bash
   unzip verilog-hdl-runner-dist.zip
   cd verilog-hdl-runner-dist
   ./install.sh
   ```

### 方法2: macOSアプリケーションバンドルで配布

1. `build_dist.sh` を実行（macOSのみ）
2. 生成された `Verilog HDL Runner.app` を配布
3. 受信者はApplicationsフォルダにドラッグ&ドロップ

### 方法3: バイナリのみ配布

```bash
# リリースビルド
cargo build --release

# バイナリを配布
# macOS/Linux: target/release/verilog-hdl-runner
# Windows: target/release/verilog-hdl-runner.exe
```

## 🔧 受信者側の必要要件

### 必須ツール

1. **Icarus Verilog** (iverilog, vvp)
   - macOS: `brew install icarus-verilog`
   - Ubuntu/Debian: `sudo apt install iverilog`
   - Windows: http://bleyer.org/icarus/

2. **GTKWave** (オプション、波形表示用)
   - macOS: `brew install gtkwave`
   - Ubuntu/Debian: `sudo apt install gtkwave`
   - Windows: http://gtkwave.sourceforge.net/

### 動作確認

```bash
# Icarus Verilogの確認
iverilog -V
vvp -V

# GTKWaveの確認（オプション）
gtkwave --version
```

## 🚀 使用方法

### 起動

```bash
# macOS/Linux（インストール済み）
verilog-hdl-runner

# macOS/Linux（ディレクトリから直接実行）
./verilog-hdl-runner

# macOS（アプリケーションバンドル）
# Applicationsフォルダからダブルクリック

# Windows
verilog-hdl-runner.exe
```

### 基本的な使い方

1. **ディレクトリ選択**: 「参照」ボタンでVerilogプロジェクトのディレクトリを選択
2. **フォルダー選択**: 左側のツリーから対象フォルダーをクリック
3. **テストベンチ選択**: 中央のリストからテストベンチファイル（`*_tb.v`）を選択
4. **依存ファイル確認**: 右側で自動検出された依存ファイルを確認（必要に応じて手動調整）
5. **実行**: 「コンパイル & 実行」ボタンをクリック

## 📋 機能一覧

- ✅ 階層的なフォルダー表示
- ✅ テストベンチファイルの自動検出
- ✅ 依存ファイルの自動検出（正規表現ベース）
- ✅ 複数ファイルのコンパイル対応
- ✅ GTKWaveによる波形自動表示
- ✅ リアルタイムログ表示
- ✅ クロスプラットフォーム対応（macOS, Linux, Windows）

## 🐛 トラブルシューティング

### アプリが起動しない（macOS）

macOSのセキュリティ設定により実行できない場合:

```bash
# 実行権限を付与
chmod +x verilog-hdl-runner

# または、「システム環境設定」→「セキュリティとプライバシー」で許可
```

### iverilogが見つからない

```bash
# PATHを確認
echo $PATH

# iverilogの場所を確認
which iverilog

# 必要に応じてPATHを追加（~/.zshrc または ~/.bashrc）
export PATH="/usr/local/bin:$PATH"
```

### フォントが表示されない（Linux）

```bash
# 日本語フォントをインストール
sudo apt install fonts-noto-cjk
```

## 📝 バイナリサイズ

最適化後のバイナリサイズ:
- macOS (arm64): 約 8-10 MB
- macOS (x86_64): 約 8-10 MB  
- Linux (x86_64): 約 8-10 MB
- Windows (x86_64): 約 8-10 MB

## 🔐 配布時の注意事項

1. **セキュリティ**: 公式リポジトリから配布することを推奨
2. **チェックサム**: SHA256ハッシュを提供
   ```bash
   shasum -a 256 verilog-hdl-runner-dist.zip
   ```
3. **署名**: macOSアプリの場合、コード署名を検討
   ```bash
   codesign -s "Developer ID" "Verilog HDL Runner.app"
   ```

## 📄 ライセンス

MIT License - 自由に配布・改変可能
