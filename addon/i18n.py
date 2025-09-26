# -*- coding: utf-8 -*-
"""Translation dictionary for Monkey hunyuan3D."""

from __future__ import annotations

import bpy

from . import ADDON_ID, get_logger

logger = get_logger()


_LOCALE_DICT = {
    "ja_JP": {
        ("*", "Prompt"): "プロンプト",
        ("*", "Prompt used for Hunyuan3D generation."): "Hunyuan3D生成で使用するプロンプト。",
        ("*", "Input Mode"): "入力モード",
        ("*", "Choose how to provide input to Hunyuan3D."): "Hunyuan3Dへの入力方法を選択します。",
        ("*", "Use text prompt only"): "テキストプロンプトのみを使用します。",
        ("*", "Use local image file (Base64)"): "ローカル画像ファイル（Base64）を使用します。",
        ("*", "Image"): "画像",
        ("*", "Local image file used as reference for generation."): "生成用の参照となるローカル画像ファイル。",
        ("*", "Result Format"): "出力形式",
        ("*", "File format of the generated asset."): "生成されたアセットのファイル形式。",
        ("*", "Download model as glTF Binary (.glb)."): "モデルを glTF バイナリ (.glb) でダウンロード。",
        ("*", "Download model as Wavefront OBJ."): "モデルを Wavefront OBJ 形式でダウンロード。",
        ("*", "Download model as Autodesk FBX."): "モデルを Autodesk FBX 形式でダウンロード。",
        ("*", "Enable PBR"): "PBRを有効化",
        ("*", "Request physically based rendering materials when supported."): "対応している場合はPBRマテリアルを要求します。",
        ("*", "Region"): "リージョン",
        ("*", "Tencent Cloud region used for the Hunyuan3D service."): "Hunyuan3Dサービスで使用するTencent Cloudのリージョン。",
        ("*", "Use the ap-guangzhou region."): "ap-guangzhouリージョンを使用します。",
        ("*", "Use the ap-shanghai region."): "ap-shanghaiリージョンを使用します。",
        ("*", "Use the ap-singapore region."): "ap-singaporeリージョンを使用します。",
        ("*", "SecretId"): "SecretId",
        ("*", "Fallback SecretId when environment variables are unavailable."): "環境変数が未設定の場合に使用するSecretId。",
        ("*", "SecretKey"): "SecretKey",
        ("*", "Fallback SecretKey when environment variables are unavailable."): "環境変数が未設定の場合に使用するSecretKey。",
        ("*", "Password"): "パスワード",
        ("*", "Password used to encrypt or decrypt stored secrets."): "暗号化ファイルの復号・保存に使用するパスワード。",
        ("*", "Storage Mode"): "保存モード",
        ("*", "How to retain secrets after input."): "入力後に秘密情報をどのように保持するかを指定します。",
        ("*", "Do not store secrets after use."): "使用後に秘密情報を保存しません。",
        ("*", "Keep secrets in memory until Blender exits."): "Blender終了までメモリ内で保持します。",
        ("*", "Encrypt secrets to an external file."): "外部ファイルに暗号化して保存します。",
        ("*", "Remember Password on Disk"): "パスワードをローカル保存",
        (
            "*",
            "Store the encryption password obfuscated on disk. Use only if you accept the risk of local compromise.",
        ): "暗号化パスワードを難読化してローカル保存します。物理侵害リスクを理解した上で利用してください。",
        ("*", "JobId"): "ジョブID",
        ("*", "Last submitted job identifier."): "最後に送信したジョブのID。",
        ("*", "Status"): "ステータス",
        ("*", "Last known status reported by the API."): "APIから通知された最新ステータス。",
        ("*", "Last Error"): "最新エラー",
        ("*", "Last error message reported by the API or importer."): "APIまたはインポーターからの最新エラーメッセージ。",
        ("*", "Monkey hunyuan3D"): "Monkey hunyuan3D",
        ("*", "Settings unavailable."): "設定を利用できません。",
        ("*", "API Authentication"): "API認証",
        ("*", "Production use of environment variables is recommended."): "本番環境では環境変数の利用を推奨します。",
        ("*", "Input (ImageBase64)"): "入力（ImageBase64）",
        ("*", "Image File"): "画像ファイル",
        (
            "*",
            "Images under 8MB after encoding are supported. Large files are recompressed automatically.",
        ): "エンコード後8MB未満の画像に対応。大きい場合は自動で再圧縮します。",
        ("*", "Generation Settings"): "生成設定",
        ("*", "Run"): "実行",
        ("*", "Status"): "ステータス",
        ("*", "JobId: {job_id}"): "ジョブID: {job_id}",
        ("*", "Status: {status}"): "ステータス: {status}",
        ("*", "Raw Status: {status}"): "生のステータス: {status}",
        ("*", "Last Error: {message}"): "最新エラー: {message}",
        ("*", "-"): "-",
        ("*", "Open API Key Page"): "APIキー管理ページを開く",
        (
            "*",
            "Open the Tencent Cloud API key management page in a browser.",
        ): "Tencent CloudのAPIキー管理ページをブラウザで開きます。",
        ("*", "Failed to open browser: {error}"): "ブラウザを開けませんでした: {error}",
        ("*", "Opened Tencent Cloud API key page."): "Tencent CloudのAPIキー管理ページを開きました。",
        ("*", "Encrypt Secrets"): "暗号化保存",
        (
            "*",
            "Encrypt and store the API secrets based on the selected storage mode.",
        ): "選択した保存モードに基づきAPI秘密情報を暗号化して保存します。",
        ("*", "SecretId/SecretKey are required."): "SecretIdとSecretKeyは必須です。",
        (
            "*",
            "NONE mode does not store secrets. They must be typed each time.",
        ): "NONEモードでは秘密情報は保存されません。毎回入力してください。",
        (
            "*",
            "Secrets stored in session memory until Blender closes.",
        ): "Blender終了までセッションメモリに保存しました。",
        ("*", "Password is required for disk mode."): "ディスクモードではパスワードが必要です。",
        ("*", "Secrets encrypted and stored on disk."): "秘密情報を暗号化してディスクに保存しました。",
        ("*", "Test Secret Decryption"): "復号テスト",
        (
            "*",
            "Test decrypting the stored secrets using the available password sources.",
        ): "利用可能なパスワードを用いて暗号化ファイルの復号テストを行います。",
        ("*", "No encrypted secret found on disk."): "暗号化された秘密情報がディスクに見つかりません。",
        ("*", "Password not available for decryption."): "復号に必要なパスワードが利用できません。",
        ("*", "Decrypted secret is empty."): "復号結果の秘密情報が空です。",
        ("*", "Decryption succeeded. Secrets are available."): "復号に成功しました。秘密情報を利用できます。",
        (
            "*",
            "Local disk storage is vulnerable; enable only if you accept the risk.",
        ): "ローカル保存は侵害に弱いため、リスクを理解したうえで有効化してください。",
        (
            "*",
            "Storing the password is your responsibility. Physical access may expose it.",
        ): "パスワード保存は自己責任です。物理アクセスで漏洩する可能性があります。",
        ("*", "Generate 3D"): "3D生成",
        (
            "*",
            "Submit a prompt to the Hunyuan3D API, then download and import the result when ready.",
        ): "Hunyuan3D APIにプロンプトを送信し、完了後に自動ダウンロードしてインポートします。",
        ("*", "No active scene found."): "アクティブなシーンが見つかりません。",
        ("*", "Settings are not available on the scene."): "シーンに設定がありません。",
        ("*", "Prompt is empty."): "プロンプトが空です。",
        ("*", "Prompt mode requires a non-empty prompt."): "プロンプトモードではプロンプトが必須です。",
        ("*", "Image mode requires a valid image file."): "画像モードでは有効な画像ファイルが必須です。",
        ("*", "Prompt and image cannot be used together."): "プロンプトと画像は同時に使用できません。",
        (
            "*",
            "Pillow (PIL) is required to encode image. Please install it into Blender's Python.",
        ): "画像エンコードにはPillow(PIL)が必要です。Blender同梱Pythonへインストールしてください。",
        (
            "*",
            "Failed to load Pillow. Use 'Install Dependencies' or check your network access.",
        ): "Pillowの読み込みに失敗しました。「依存関係をインストール」を実行するかネットワークを確認してください。",
        ("*", "Image file could not be read."): "画像ファイルを読み込めませんでした。",
        ("*", "Image is too large. Ensure the encoded size is under 8MB."): "画像が大きすぎます。エンコード後8MB未満にしてください。",
        ("*", "Failed to prepare image: {error}"): "画像の準備に失敗しました: {error}",
        ("*", "Prompt Source"): "プロンプト入力元",
        ("*", "Inline"): "インライン",
        ("*", "Text Block"): "テキストブロック",
        ("*", "External File"): "外部ファイル",
        ("*", "Prompt File"): "プロンプトファイル",
        ("*", "Open Text Editor"): "テキストエディタを開く",
        (
            "*",
            "Open a separate Text Editor window for prompt editing.",
        ): "プロンプト編集用のテキストエディタを別ウィンドウで開きます。",
        ("*", "New Text"): "新規テキスト",
        ("*", "Save Text to File"): "テキストをファイルに保存",
        ("*", "Load File to Text"): "ファイルをテキストに読み込み",
        ("*", "No text block selected."): "テキストブロックが選択されていません。",
        ("*", "File path is empty."): "ファイルパスが空です。",
        ("*", "Failed to read prompt from file."): "ファイルからプロンプトを読み込めませんでした。",
        ("*", "Failed to open Text Editor window."): "テキストエディタウィンドウを開けませんでした。",
        ("*", "UTF-8 expected. CRLF normalized."): "UTF-8形式を想定。CRLFはLFに正規化されます。",
        (
            "*",
            "Failed to install Tencent Cloud SDK: {error}",
        ): "Tencent Cloud SDKのインストールに失敗しました: {error}",
        (
            "*",
            "Failed to import Tencent Cloud SDK after installation attempt.",
        ): "Tencent Cloud SDKをインストール後に読み込めませんでした。",
        (
            "*",
            "API keys missing: set environment variables or fill SecretId/SecretKey.",
        ): "APIキー未設定：環境変数 または Nパネルの SecretId/SecretKey を設定してください。",
        ("*", "API error during submission: {error}"): "送信中にAPIエラーが発生: {error}",
        ("*", "Unexpected error during submission: {error}"): "送信中に予期しないエラーが発生: {error}",
        ("*", "Job submitted. Tracking in the status panel."): "ジョブを送信しました。ステータス欄で確認できます。",
        ("*", "API error while querying job: {error}"): "ステータス確認中にAPIエラーが発生: {error}",
        ("*", "Network error while querying job: {error}"): "ステータス確認中にネットワークエラーが発生: {error}",
        ("*", "No download URL returned by the service."): "サービスからダウンロードURLが返されませんでした。",
        ("*", "Network error while downloading file: {error}"): "ダウンロード中にネットワークエラーが発生: {error}",
        ("*", "Import failed: {error}"): "インポートに失敗しました: {error}",
        (
            "*",
            "Generation failed. Review your prompt and output format.",
        ): "生成に失敗しました。プロンプトや出力形式を見直してください。",
        ("*", "Environment Variables"): "環境変数",
        ("*", "TENCENTCLOUD_SECRET_ID: {status}"): "TENCENTCLOUD_SECRET_ID: {status}",
        ("*", "TENCENTCLOUD_SECRET_KEY: {status}"): "TENCENTCLOUD_SECRET_KEY: {status}",
        ("*", "Secrets typed in the panel are session-only and not saved."): "Nパネルで入力した秘密鍵はセッション限定で保存されません。",
        ("*", "Set environment variables for production use."): "本番運用では環境変数を設定してください。",
        ("*", "Prompt parameter name in API"): "APIのプロンプトパラメータ名",
        (
            "*",
            "Override the parameter name sent to the API when submitting prompt input.",
        ): "プロンプト入力送信時にAPIへ渡すパラメータ名を上書きします。",
        ("*", "Install Dependencies"): "依存関係をインストール",
        (
            "*",
            "Install Pillow and Tencent Cloud SDK into the add-on vendor folder.",
        ): "PillowとTencent Cloud SDKをアドオンのvendorフォルダにインストールします。",
        (
            "*",
            "Failed to install dependencies: {error}",
        ): "依存関係のインストールに失敗しました: {error}",
        (
            "*",
            "Dependencies installed successfully.",
        ): "依存関係のインストールに成功しました。",
        ("*", "Set"): "設定済み",
        ("*", "Not set"): "未設定",
        ("*", "Submitting"): "送信中",
        ("*", "Submitted"): "送信済み",
        ("*", "Queued"): "キュー待ち",
        ("*", "Pending"): "保留",
        ("*", "Processing"): "処理中",
        ("*", "Running"): "実行中",
        ("*", "Done"): "完了",
        ("*", "Importing"): "インポート中",
        ("*", "Imported"): "インポート済み",
        ("*", "Failed"): "失敗",
        ("*", "Error"): "エラー",
        ("*", "Unknown"): "不明",
    }
}


def register() -> None:
    bpy.app.translations.register(ADDON_ID, _LOCALE_DICT)
    logger.info("Translations registered.")


def unregister() -> None:
    try:
        bpy.app.translations.unregister(ADDON_ID)
        logger.info("Translations unregistered.")
    except Exception:
        pass
