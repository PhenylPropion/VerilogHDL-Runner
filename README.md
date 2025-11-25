# Verilog HDL Runner

GUIベースのVerilogシミュレーション実行ツール


[ダウンロードリンク](https://github.com/PhenylPropion/VerilogHDL-Runner/releases/tag/2.1_ver_Python#:~:text=Verilog_HDL_Runner.py)


## 推奨
VScode の " Code Runner " 拡張機能の使用を強くおすすめします。
[Code Runner 拡張機能](https://marketplace.visualstudio.com/items?itemName=formulahendry.code-runner)
<img width="700" height="500" alt="スクリーンショット 2025-09-24 9 05 07" src="https://github.com/user-attachments/assets/4d877fc5-226d-4dd1-aecd-c1ef2287323d" />
<img width="700" height="500" alt="スクリーンショット 2025-09-24 9 03 14" src="https://github.com/user-attachments/assets/c3f4f162-b775-46f6-ae43-2aff7b4945aa" />

## 概要

Verilog HDL Runnerは、VerilogファイルのコンパイルとシミュレーションをGUIで簡単に実行できるPythonスクリプトです。  
フォルダー構造をツリービューで表示し、複数のディレクトリに散らばったVerilogファイルを効率的に管理・実行できます。

## 機能

### フォルダー管理

- **ツリービュー表示**: Verilogファイルが含まれるフォルダーを階層表示
- **ディレクトリ選択**: 参照ボタンで作業ディレクトリを簡単に変更
- **自動検索**: サブディレクトリを再帰的にスキャンしてVerilogファイルを発見

### コンパイル・実行

- **iverilogコンパイル**: 自動的に`iverilog -Wall -o $name $name_tb.v $name.v`を実行
- **vvpシミュレーション**: コンパイル成功後に`vvp $name`を実行
- **エラーハンドリング**: 詳細なエラーメッセージを表示

### 波形表示

- **GTKWave連携**: チェックボックスでON/OFF可能（デフォルト有効）
- **自動起動**: シミュレーション成功後に`gtkwave $name.vcd`を実行
- **バックグラウンド実行**: メインGUIをブロックしない

### ユーザーインターフェース

- **分割ビュー**: フォルダーツリーとファイルリストを並列表示
- **リアルタイムログ**: 実行結果をスクロール可能なテキストエリアに表示
- **ログクリア**: 出力エリアの内容を簡単にクリア

## 必要環境

### ソフトウェア要件

- **Python 3.6以上**
- **Icarus Verilog 環境** (`iverilog`, `vvp`)
- **GTKWave** （波形表示用、オプション）

### Pythonライブラリ

```python
tkinter  # 標準ライブラリ（通常は自動インストール）
```

## Verilog HDL 及び依存環境のセットアップ

### 1. Icarus Verilogのインストール

#### macOS (Homebrew)

```bash
brew install icarus-verilog
```

#### Ubuntu/Debian

```bash
sudo apt-get install iverilog
```

#### Windows

[Icarus Verilog公式サイト](http://iverilog.icarus.com/)からダウンロード

### 2. GTKWave のインストール（オプション）

#### macOS

```bash
brew install gtkwave
```

#### Linux

```bash
sudo apt-get install gtkwave
```

### 3. アプリケーションの起動

```bash
python Verilog_HDL_Runner.py
```

## 使用方法

### 基本的な使い方

1. **アプリケーション起動**

   ```bash
   python Verilog_HDL_Runner.py
   ```
VScode の " Code Runner " 拡張機能の使用を強くおすすめします。
[Code Runner 拡張機能](https://marketplace.visualstudio.com/items?itemName=formulahendry.code-runner)

2. **ディレクトリ選択**

   - 上部の「参照」ボタンをクリック
   - Verilogファイルが含まれるルートディレクトリを選択

3. **ファイル選択**

   - 左側のツリービューでフォルダーを選択
   - 右側のリストから実行したいVerilogファイルを選択

4. **実行**

   - 「GTKWaveで波形表示」のチェック状態を確認
   - 「コンパイル & 実行」ボタンをクリック

### ファイル命名規則

このツールは以下の命名規則を前提としています：

```text
module_name.v        # メインのVerilogファイル
module_name_tb.v     # テストベンチファイル
module_name.vcd      # シミュレーション結果（自動生成）
```

例：

```text
xor3.v               # XOR3ゲートの実装
xor3_tb.v            # XOR3ゲートのテストベンチ
xor3.vcd             # シミュレーション波形データ
```

## 実行例

### サンプルディレクトリ構造

```text
logic/
├── Archive/
│   └── Vol2/
│       ├── add1.v
│       ├── add1_tb.v
│       └── ...
└── vol1/
    ├── xor3.v
    └── xor3_tb.v
```

### 実行ログ例

```text
=== xor3 の実行を開始 (/Users/logic/vol1) ===
実行中: iverilog -Wall -o xor3 xor3_tb.v xor3.v
コンパイル成功
実行中: vvp xor3
シミュレーション結果:
VCD info: dumpfile xor3.vcd opened for output.
実行中: gtkwave xor3.vcd
GTKWaveを起動しました (PID: 12345)
実行ファイル 'xor3' を削除しました。
=== xor3 の実行完了 ===
```

## 機能詳細

### フォルダーツリー

- Verilogファイル（`.v`）が存在するディレクトリのみを表示
- テストベンチファイル（`_tb.v`）は除外してメインファイルの存在をチェック
- 隠しディレクトリ（`.`で始まるディレクトリ）は除外

### ファイルフィルタリング

- メインのVerilogファイル（`*.v`）のみを表示
- テストベンチファイル（`*_tb.v`）は自動で除外
- ファイル選択時に対応するテストベンチファイルの存在を確認

### エラーハンドリング

- **ファイル不存在**: メインファイルまたはテストベンチファイルが見つからない場合
- **コンパイルエラー**: iverilogの構文エラーやワーニング
- **実行エラー**: vvpの実行時エラー
- **ツール不存在**: iverilog、vvp、gtkwaveが見つからない場合

## トラブルシューティング

### よくある問題

#### 1. `iverilog`が見つからない

```text
エラー: iverilogが見つかりません。Icarus Verilogがインストールされているか確認してください。
```

**解決策**: Icarus Verilogをインストールし、PATHに追加してください。

#### 2. テストベンチファイルが見つからない

```text
エラー: testbenchファイル 'module_name_tb.v' が見つかりません。
```

**解決策**: `module_name_tb.v`ファイルが同じディレクトリに存在することを確認してください。

#### 3. VCDファイルが生成されない

```text
警告: VCDファイル 'module_name.vcd' が見つかりません。波形表示をスキップします。
```

**解決策**: テストベンチファイルに`$dumpfile`と`$dumpvars`の記述があることを確認してください。

```verilog
initial begin
    $dumpfile("module_name.vcd");
    $dumpvars(0, module_name_tb);
end
```

#### 4. GTKWaveが起動しない

**macOS**: XQuartzがインストールされていることを確認  
**Linux**: X11環境が正しく設定されていることを確認

### カスタマイズ

コンパイルオプションや実行パラメータは、対応するメソッド内で変更可能です。

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。

詳細は以下のファイルをご確認ください：

- [LICENSE](LICENSE) - 英語版 & 日本語版

## 貢献

バグ報告や機能提案は、GitHubのIssueでお知らせください。プルリクエストも歓迎します。

---

**作者**: Yonghao Huo 
**バージョン**: 1.0.1 
**最終更新**: 2025年9月23日
