# 文字化け修正について

## 問題
Rust版のeguiアプリケーションで絵文字や日本語が文字化けする可能性がある。

## 修正内容

### 1. 絵文字の削除
- UIの絵文字アイコン（📁🧪📄など）をテキストに置き換え
- ログメッセージの絵文字（✓❌⚡など）をASCII記号に置き換え

### 2. フォント設定の追加
```rust
// main関数内でフォントを設定
let mut fonts = egui::FontDefinitions::default();

#[cfg(target_os = "macos")]
{
    // macOSではヒラギノフォントを使用
    if let Ok(font_data) = std::fs::read("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc") {
        fonts.font_data.insert(
            "HiraginoSans".to_owned(),
            egui::FontData::from_owned(font_data),
        );
        
        fonts.families.entry(egui::FontFamily::Proportional)
            .or_default()
            .insert(0, "HiraginoSans".to_owned());
    }
}

cc.egui_ctx.set_fonts(fonts);
```

### 3. ログメッセージの変更

| 変更前 | 変更後 |
|--------|--------|
| `🚀 実行を開始` | `[開始] 実行` |
| `✓ コンパイル成功` | `[OK] コンパイル成功` |
| `❌ エラー` | `[ERROR]` |
| `⚠️  警告` | `[WARN]` |
| `📊 シミュレーション結果` | `[OUTPUT] シミュレーション結果` |
| `📈 gtkwave` | `[WAVE] gtkwave` |
| `🗑️  削除` | `[CLEAN] 削除` |

### 4. UIラベルの変更
- フォルダーアイコン: `📁 folder` → `[folder]`
- テストベンチ: `🧪 file.v` → `file.v`
- 依存ファイル: `📄 file.v` → `file.v`

## ビルド方法
```bash
cargo build --release
```

## 実行方法
```bash
./target/release/verilog-hdl-runner
```

## 互換性
- macOS: ヒラギノフォントで日本語表示
- Linux/Windows: システムデフォルトフォント
