# Blenderアドオン用 API秘密情報管理 仕様

- version: 1.0
- title: "Blenderアドオン用 API秘密情報管理 仕様"
- status: "draft"
- owner: "Sakaki Masamune"

## Overview
本仕様は、Blenderアドオンで扱う外部APIキー・シークレット等の秘密情報を安全かつ実用的に取り扱うための設計指針を示す。最大の要件は「.blendファイルやアドオン本体に秘密情報を残さない」ことであり、安全性と利便性の両立を目指す。

---

## Design Principles
- .blend ファイルやアドオン内に秘密情報を保持しない
- 秘密情報はユーザー入力または暗号化した外部ファイルから取得する
- パスワード保存を希望する場合は自己責任とし、UIでリスクを明示する
- 秘密ファイルはアドオン外 (`~/.config/fooni/`) に作成し、権限は 600 に設定する

---

## Storage Modes
| Mode | Description | Security | Usability |
|------|-------------|----------|-----------|
| NONE | 毎回パスワード入力 | ★★★★☆ | ★☆☆☆☆ |
| SESSION | Blender起動中のみメモリ保持 | ★★★☆☆ | ★★★☆☆ |
| DISK | 暗号化してローカル保存（自己責任） | ★★☆☆☆ | ★★★★☆ |

---

## UI Behavior
- モード選択を EnumProperty として提供
- DISK モード選択時には注意文をアイコン付きで表示

---

## Encrypted File Specification
- **保存パス**: `~/.config/fooni/secret.enc`
- **フォーマット構造**: `MAGIC(4) + VERSION(1) + FLAG(1) + SALT(16) + NONCE(12) + CIPHERTEXT + TAG(16)`
- **コンテンツ**: 秘密情報は JSON 形式で格納
- **暗号方式**:
  - プライマリ: AES-256-GCM（cryptography）
  - フォールバック: scrypt + HMAC + XOR（依存なし）
- **ファイルパーミッション**: 600（ユーザーのみ読み書き可）

---

## Password Handling
### 入力
- Nパネルで PASSWORD サブタイプ欄に入力
- ボタン押下後は UI 上の入力欄を必ずクリア

### 保存
- **セッション**: `_session_password` に保持し、Blender終了時に破棄
- **ディスク**:
  - `~/.config/fooni/.pwd.key`: ランダム鍵（32バイト）
  - `~/.config/fooni/.pwd`: XOR難読化＋HMAC付きパスワード本体
- **注意**: 物理アクセスで漏洩の可能性あり。UIに警告表示

---

## UI Specification
- Password（PASSWORD）
- 保存モード（EnumProperty: NONE / SESSION / DISK）
- 暗号化保存（Operator）
- 復号テスト（Operator）
- DISK選択時警告: ※ローカル保存は侵害に弱いので自己責任で使用してください

---

## Operation Flow
1. ユーザーがパスワードと保存モードを選択
2. 暗号化保存ボタン押下 → AES-GCM等で暗号化 → 外部ファイルに保存（600）
3. API使用時、以下の優先順で復号を試行
   1. UI入力
   2. セッションメモリ
   3. ディスク保存
4. 復号失敗時はエラーメッセージ表示

---

## Security Notes
- .blend や .py に秘密情報を含めない
- DISK モードは物理アクセス時に突破される可能性があるため NONE / SESSION を推奨
- 入力欄は常に即時クリア
- ディレクトリごとコピーされる可能性を考慮し、ポータブルモードでは .pwd を生成しない

---

## Future Extensions
- OS キーチェーン（DPAPI / Keychain）対応
- パスワード強度チェック
- ラベル付き秘密情報管理（複数API対応）
- 暗号化ファイルのバックアップ・リストア CLI ツール

---

## Implementation Memo
- cryptography ライブラリ利用時は vendor 自動インストール対応を併用する
- `pip install --target ~/.config/fooni/vendor cryptography`
- 自動化が難しい環境ではフォールバック方式を適用

