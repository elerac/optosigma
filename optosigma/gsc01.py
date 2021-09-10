from typing import Tuple, Union
import serial

class GSC01(serial.Serial):
    def raw_command(self, cmd: str) -> Union[bool, str]:
        """コントローラにコマンドを送信

        成功すると"OK"，失敗すると"NG"がコントローラ側から送られてくる．
        そこで，"OK"はTrue，"NG"はFalseと変換して返す．
        例外として，"OK"や"NG"以外の文字列が送られてきた場合は，そのままの文字列を返す．

        Parameters
        ----------
        cmd : str
            コマンドの内容は，GSC-01の取扱説明書を参考にすること．

        Returns
        -------
        ret : bool or str
            OKなら``True``，NGなら``False``
        """
        self.write(cmd.encode())
        self.write(b"\r\n")
        return_msg = self.readline().decode()[:-2]  # -2: 文字列に改行コードが含まれるため，それ以外を抜き出す．
        return (      True if return_msg == "OK"
                else False if return_msg == "NG" 
                else return_msg)
                
    def get_position(self) -> int:
      return self.get_status1()[0]

    @property
    def position(self) -> int:
        return self.get_position()

    @property
    def ack1(self) -> str:
        """
        ACK1:  X  コマンドエラー
               K  コマンド正常受付
        """
        return self.get_status1()[1]

    @property
    def ack2(self) -> str:
        """
        ACK2:  L  リミットセンサで停止
               K  正常停止
        """
        return self.get_status1()[2]

    @property
    def ack3(self) -> str:
        """
        ACK3:  B  Busy 状態
               R  Ready 状態
        """
        return self.get_status2()

    @property
    def is_ready(self) -> bool:
        """ステージがReady状態かをチェック
        """
        ack3 = self.ack3
        if ack3 == "R":
            return True
        elif ack3 == "B":
            return False

    @property
    def is_last_command_success(self) -> bool:
        """最後に実行したコマンドが正常受け付けられたかをチェック
        """
        ack1 = self.ack1
        if ack1 == "K":
            return True
        elif ack1 == "X":
            return False

    def return_origin(self) -> bool:
        """H コマンド(機械原点復帰命令)

        ステージにある機械原点を検出し、その位置を原点とします。
        機械原点を検出後に座標値は 0 となります。
        移動速度は固定で S:500pps、F:5000pps、R:200mS となります。
        原点復帰動作中に停止命令が行われた場合、原点復帰動作は中断します。
        原点復帰動作中に定められたシーケンス以外のリミットセンサを検出した場合、原点復帰動作を中断します。
        機械原点復帰動作中は停止命令と確認命令以外は受け付けません。リミットセンサ検出時には 減速動作を行いません。
        
        駆動方向が正転の場合のリミットセンサは次のように割り当てられます。  
          1)LS0  CCW(+)
          2)LS1  CW(-)
        駆動方向が逆転の場合のリミットセンサは次のように割り当てられます。  
          1)LS0  CCW(-)
          2)LS1  CW(+)
        励磁が OFF の場合、エラーになり原点復帰動作は行われません。

        ・コマンド形式
          H:1     機械原点復帰実施 
          H:W     機械原点復帰実施
        """
        return self.raw_command("H:1")
        
    def set_relative_pulse(self, pulse: int) -> bool:
        """M コマンド(相対移動パルス数設定命令)

        ステージの移動量と移動方向を設定します。
        本コマンド実行後、駆動命令の実行で実際のステージ駆動を行います。
        動作は速度設定命令で設定された加減速動作を行います。
        駆動命令を実行せずに本命令を続けて実行した場合は最後に実行した本命令又は“絶対移動パルス設定命令”が有効になります。
        また、“原点復帰命令”や“ジョグ命令”、“停止命令”が実行された場合、 本命令で設定された値は無効になります。
        移動後の座標が仕様範囲(± 16,777,215)を超える場合はコマンドエラーになります。
        励磁が OFF の状態で本命令を実行した場合、コマンドエラーになります。
        
        ・コマンド形式
          M:nmPx
        
        ・パラメータ
          n:1又W           動作軸名 1 又は W を指定して下さい。
          m:+又は-        　+にて+方向設定、-にて-方向設定
          x:移動パルス数     0 ~ 16,777,215 の値が設定可能
          
        例) M:1+P1000      +方向に 1000 パルス移動を設定
        　  M:W-P5000      -方向に 5000 パルス移動を設定
        """
        n = 1
        m = "+" if pulse >= 0 else "-"
        x = str(abs(pulse))
        return self.raw_command(f"M:{n}{m}P{x}")

    def set_absolute_pulse(self, pulse: int) -> bool:
        """A コマンド(絶対移動パルス数設定命令)

        原点からの座標位置にステージの移動量と移動方向を設定します。
        本コマンド実行後、駆動命令の実行で実際のステージ駆動を行います。
        動作は速度設定命令で設定された加減速動作を行います。
        駆動命令を実行せずに本命令を続けて実行した場合は最後に実行した本命令又は“相対移動パルス設定命令”が有効になります。
        また、“原点復帰命令”や“ジョグ命令”、“停止命令” が実行された場合、本命令で設定された値は無効になります。
        移動後の座標が仕様範囲(± 16,777,215)を超える場合はコマンドエラーになります。
        励磁が OFF の状態で本命令を実行した場合、コマンドエラーになります。

        ・コマンド形式
          A:nmPx
        
        ・パラメータ
          n:1又W           動作軸名 1 又は W を指定して下さい。
          m:+又は-        　+にて+方向設定、-にて-方向設定
          x:移動パルス数     0 ~ 16,777,215 の値が設定可能
          
        例) A:1+P1000      +1000 パルス座標へ移動を設定
        　  A:W-P5000      -5000 パルス座標へ移動を設定
        """
        n = 1
        m = "+" if pulse >= 0 else "-"
        x = str(abs(pulse))
        return self.raw_command(f"A:{n}{m}P{x}")

    def jog(self, direction: str) -> bool:
        """J コマンド(ジョグ運転命令)

        ステージのジョグ運転を設定します。
        本コマンド実行後、駆動命令の実行で実際のステージ駆動を行います。
        動作は設定されたジョグ速度で駆動し、加減速動作は行いません。
        ジョグ速度は“ジョグ運転速度設定命令”で設定します。
        停止させる場合は、L コマンド(停止命令)にて停止をします。(L コマンドが無い場合は、リミットセンサまで移動してリミットセンサに て停止します。)
        駆動命令を実行せずに他の移動命令(“相対移動パルス数設定命令”等)を実行した場合、本命令は取り消されます。
        励磁が OFF の状態で本命令を実行した場合、コマンドエラーになります。

        ・コマンド形式
          J:nm

        ・パラメータ
          n:1又はW     動作軸名 1 又は W を指定して下さい。
          m:+又は-     +にて+方向設定、-にて-方向設定

        例) J:1+     +方向のジョグ運転を設定
        """
        if direction in ["+", "-"]:
            n = 1
            m = direction
            return self.raw_command(f"J:{n}{m}")
        else:
            msg = f'"{direction}" is not supported, choose direction from "+" or "-"'
            raise ValueError(msg)

    def driving(self) -> bool:
        """G コマンド(駆動命令)

        ステージの駆動動作を行います。
        駆動動作は直前に実行された、“相対 / 絶対移動パルス数設 定命令”、“ジョグ運転命令”に従って行われます。
        ステージの駆動中、リミットが検出された場合は直ちにステージ駆動を停止します。その際には加減速動作は行いません。
        移動命令(“相対 / 絶対移動パルス数設定命令”、“ジョグ運転命令”)が実行されないで本命令を実行した場合、コマンドエラーになります。
        励磁が OFF の状態で本命令を実行した場合、コマンドエラーになります。
        
        ・コマンド形式
          G:     駆動開始
          
        例) M:1+P1000   
        　  G:            +方向に 1000 パルス移動する
        """
        return self.raw_command("G:")

    def decelerate_stop(self) -> bool:
        """L コマンド(減速停止命令)

        ステージを減速停止させます。

        ・コマンド形式
          L:1     減速停止 
          L:W     減速停止
        """
        return self.raw_command("L:1")

    def immediate_stop(self) -> bool:
        """L:E コマンド(即停止命令)

        ステージを即停止させます。
        非常停止信号の入力時と異なり、励磁の OFF は行いません。

        ・コマンド形式
          L:E     即停止実施
        """
        return self.raw_command("L:E")

    def set_logical_zero(self) -> bool:
        """R コマンド(論理原点設定命令)

        現在の座標を電気(論理)原点に設定します。
        本コマンド実行後、現在位置は“0”になります。

        ・コマンド形式
          R:1     論理原点を設定実施 
          R:W     論理原点を設定実施
        """
        return self.raw_command("R:1")

    def set_speed(self, spd_min: int, spd_max: int, acceleration_time: int) -> bool:
        """D コマンド(速度設定命令)

        ステージ移動時の最小速度、最大速度、加減速時間を設定します。
        最小速度は運転速度 S としてステージの起動時の速度です。
        最大速度は運転速度 F としてステージの最大速度を規定します。
        これらの単位は[PPS]です。
        加減速時間は加速時は運転速度 S から運転速度 F までの時間を、減速時は運転速度 F から運転速度 S までの時間を規定します。
        この単位は[mS]で す。電源投入時には、最小速度(S)500PPS、最大速度(F)5000PPS、加減速時間(R) 200mS が設定されています。(設定プログラムにて、速度初期値を変更した場合は、その値に従います。)
        最大速度 F は必ず最小速度 S 以上の値を設定して下さい。
        速度の設定は 100[PPS]単位で行って下さい、100[PPS]未満の値は切り捨てられます。

        ・コマンド形式
          D:nSspd1Fspd2Rspd3

        ・パラメータ
          n:1又W                   動作軸名 1 又は W を指定して下さい。
          spd1:最小速度(S)設定　     設定範囲:100 ~ 20000(単位:PPS) 
          spd2:最大速度(F)設定　     設定範囲:100 ~ 20000(単位:PPS) 
          spd3:加減速時間(R)設定     設定範囲:0 ~ 1000(単位:mS)
          
        例) D:1S500F5000R200     最小速度 S500[PPS], 最大速度 F5000[PPS], 加減速時間 R200[mS]に設定します。
        """
        n = 1
        spd1 = spd_min
        spd2 = spd_max
        spd3 = acceleration_time
        return self.raw_command(f"D:{n}S{spd1}F{spd2}R{spd3}")

    def energize_motor(self, energize: bool) -> bool:
        """C コマンド(励磁 ON/OFF 命令)

        モータを励磁又は、励磁を解除する命令です。

        ・コマンド形式
          C:nm

        ・パラメータ
          n:1又W　     動作軸名 1 又は W を指定して下さい。
          m:0又は1     0 にて励磁 OFF、1 にて励磁 ON
          
        例) C:10     モータを励磁 OFF に設定
        """
        n = 1
        m = 1 if energize else 0
        return self.raw_command(f"C:{n}{m}")

    def get_status1(self) -> Tuple[int, str, str, str]:
        """Q コマンド(ステータス確認 1 命令)

        本機からステージ動作状況や座標値等を返送します。

        ・コマンド形式
          Q:

        ・リターン  -  1000、ACK1、ACK2、ACK3 
                   座標値
                        ACK1:  X  コマンドエラー
                               K  コマンド正常受付
                        ACK2:  L  リミットセンサで停止
                               K  正常停止
                        ACK3:  B  Busy 状態
                               R  Ready 状態
        *)返送データの座標値は符号を含めて 10 桁固定です。(符号左詰め、座標値右詰め)
        """
        status = self.raw_command("Q:").split(",")
        position = int(status[0].replace(" ", ""))
        ack1 = status[1]
        ack2 = status[2]
        ack3 = status[3]
        return position, ack1, ack2, ack3

    def get_status2(self) -> str:
        """! コマンド(ステータス確認 2 命令)

        本機から ACK3 の状況(ステージ移動状況)を返送します。

        ・コマンド形式
          !:
        
        ・リターン
          B  Busy 状態
          R  Ready 状態
        """
        return self.raw_command("!:")

    def get_version(self, firmware_type: str="ROM") -> str:
        """? コマンド(内部情報取得命令)

        ・コマンド形式
          ?:V

        ・リターン例 
          V1.00     ROM バージョン Ver1.00
          
        ・コマンド形式
          ?:- 
        
        ・リターン例 
          001     リビジョン番号 001
        """
        if firmware_type.lower() == "rom":
            return self.raw_command("?:V")
        elif firmware_type.lower() == "revision":
            return self.raw_command("?:-")
        else:
            msg = f'"{firmware_type}" is not supported, choose firmware type from "ROM" or "Revision"'
            raise ValueError(msg)

    def io_output(self, a: int) -> bool:
        """O コマンド(I/O 出力命令)

        I/O 出力ポートの状態を設定します。ポートの状態は 0 ~ 15 までの数値で設定します。
        
        ・コマンド形式
          O:a

        ・パラメータ
          a:0 ~ 15 

        例) O:1     I/O 出力ポート DO0 を“ON”にします
        """
        return self.raw_command(f"O:{a}")

    def io_input(self) -> int:
        """I コマンド(I/O 入力確認命令)

        I /O 入力ポートの状態を確認します。ポートの状態は 0 ~ 15 までの数値で返信します。

        ・コマンド形式
          I:

        例) I:  
        　  リターン:2  I/O 入力ポート DI1 のみ“ON”です
        """
        return int(self.raw_command("I:"))