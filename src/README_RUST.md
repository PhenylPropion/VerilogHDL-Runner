# Verilog HDL Runner (Rust版)

Rustで実装されたモダンなVerilog HDLコンパイル・実行ツール

## 特徴

- 🚀 **高速**: Rustの性能を活かした高速動作
- 🎨 **モダンUI**: eguiによるクロスプラットフォームGUI
- 🔍 **自動依存検出**: テストベンチから必要なファイルを自動検出
- 📊 **GTKWave統合**: 波形ビューアの自動起動
- 📁 **階層的フォルダー表示**: プロジェクト構造を視覚化

## 必要要件

- Rust (1.70以上)
- Icarus Verilog (`iverilog`, `vvp`)
- GTKWave (オプション)

## ビルド方法

```bash
# デバッグビルド
cargo build

# リリースビルド（最適化）
cargo build --release
```

## 実行方法

```bash
# デバッグモード
cargo run

# リリースモード
cargo run --release

# または直接実行
./target/release/verilog-hdl-runner
```

## 使い方

1. **ディレクトリ選択**: 「📁 参照」ボタンでプロジェクトディレクトリを選択
2. **フォルダー選択**: 左側のツリーから対象フォルダーをクリック
3. **テストベンチ選択**: 中央のリストからテストベンチファイルを選択
4. **依存ファイル確認**: 右側で自動選択された依存ファイルを確認（手動調整可能）
5. **実行**: 「▶️ コンパイル & 実行」ボタンをクリック

## 対応コマンド

```bash
# 以下のようなコマンドに対応
iverilog -Wall -o add1 add1_tb.v add1.v half_adder.v
vvp add1
gtkwave add1.vcd &
```

## Python版との違い

- **パフォーマンス**: より高速な起動と実行
- **メモリ効率**: Rustの所有権システムによる効率的なメモリ管理
- **クロスプラットフォーム**: macOS、Linux、Windowsで同じUIを提供
- **型安全**: コンパイル時の型チェックによる堅牢性

## ライセンス

MIT License
