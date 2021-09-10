# OptoSigma Motorized Stages Control

[シグマ光機の自動ステージ](https://jp.optosigma.com/ja_jp/motorized-stages.html)をPythonから動かします．研究室用に作成．

## 対応機種
### コントローラ
- 1軸ステージコントローラ / GSC-01 [[Web]](https://jp.optosigma.com/ja_jp/motorized-stages/controllers-drivers/single-axis-stage-controller/gsc-01.html) [[Manual]](https://jp.optosigma.com/html/jp/software/motorize/manual_jp/GSC-01.pdf)
- 2軸ステージコントローラ / GSC-02 [[Web]](https://jp.optosigma.com/ja_jp/motorized-stages/controllers-drivers/2-axis-stage-controller-half-step/gsc-02.html) [[Manual]](https://jp.optosigma.com/html/jp/software/motorize/manual_jp/GSC-02.pdf) 

### ステージ
- 自動回転ステージ / OSMS-60YAW [[Web]](https://jp.optosigma.com/ja_jp/osms-60yaw.html) [[PDF]](https://jp.optosigma.com/html/ja/page_pdf/SGSP-40_60YAW.pdf)
- 自動偏光子ホルダーφ１００用 / PWA-100 [[Web]](http://www.twin9.co.jp/product/holders-list/mirror-list-2-2/pwa-100/)

## 必要なPythonモジュール
* [pySerial](https://github.com/pyserial/pyserial)

## 使い方

### 回転ステージ（PWA100, OSMS-60YAW）
#### インスタンスの作成
インスタンスの作成時に接続要求が行われます．コンストラクタに渡すシリアルポート名は，環境によって下の例と違うため．自分の環境に応じて適宜確認してください．
```python
from optosigma import PWA100
polarizer = PWA100("/dev/tty.usbserial-FTRWB1RN")
```

```python
from optosigma import OSMS60YAW
polarizer = OSMS60YAW("/dev/tty.usbserial-FTRWB1RN")
```

#### リセット
ステージを機械原点に復帰させます．
```python
polarizer.reset()
```

#### 回転角度
`degree` は実際のステージの回転角度と連動しています．
```python
print(polarizer.degree)  # 現在の回転角度を取得
polarizer.degree = 90    # 回転角度が90[deg]になるように回転
polarizer.degree += 60   # 回転角度が現在の角度から+60[deg]になるように回転
```

#### 移動中に別の動作を行う
`reset`や`degree`でのステージの移動において，デフォルトでは移動が完了するまで待つ処理を行っています．移動中にも別の処理を行いたい場合は，メンバ変数`is_sleep_until_stop`を`False`に設定してください．
```python
polarizer.is_sleep_until_stop = False  # 移動完了を待つフラグをFalseにする
polarizer.degree += 180  # 移動開始（移動完了を待たずに次の処理に行く）
"""ここに移動中に行う処理を書く"""
polarizer.sleep_until_stop()  # 明示的に移動完了を待つ
```