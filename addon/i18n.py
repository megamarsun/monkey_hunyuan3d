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
        ("*", "Last Error: {message}"): "最新エラー: {message}",
        ("*", "-"): "-",
        ("*", "Open API Key Page"): "APIキー管理ページを開く",
        (
            "*",
            "Open the Tencent Cloud API key management page in a browser.",
        ): "Tencent CloudのAPIキー管理ページをブラウザで開きます。",
        ("*", "Failed to open browser: {error}"): "ブラウザを開けませんでした: {error}",
        ("*", "Opened Tencent Cloud API key page."): "Tencent CloudのAPIキー管理ページを開きました。",
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
        ("*", "Image file could not be read."): "画像ファイルを読み込めませんでした。",
        ("*", "Image is too large. Ensure the encoded size is under 8MB."): "画像が大きすぎます。エンコード後8MB未満にしてください。",
        ("*", "Failed to prepare image: {error}"): "画像の準備に失敗しました: {error}",
        (
            "*",
            "SDK not installed: run 'pip install tencentcloud-sdk-python' in Blender's Python.",
        ): "SDK未導入：Blender 同梱Pythonで 'pip install tencentcloud-sdk-python' を実行してください。",
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
