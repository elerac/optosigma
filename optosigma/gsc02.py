from typing import Tuple, Union, Sequence, Any
import serial

class GSC02(serial.Serial):
    def raw_command(self, cmd: str) -> Union[bool, Any]:
        """コントローラにコマンドを送信

        Parameters
        ----------
        cmd : str
            コマンドの内容は，GSC-02の取扱説明書を参考にすること．

        Returns
        -------
        ret : bool or Any
            状態確認系コマンド(Q、!、?)の場合は，コントローラやステージの状態を返送
            それ以外のコマンドの場合は，コマンド正常に受け付けられたかどうか，TrueかFalseを返送
        """
        self.write(cmd.encode())
        self.write(b"\r\n")
        
        if cmd[:2] in ["Q:", "!:", "?:"]:
            # 状態確認系コマンド(Q、!、?)
            return self.readline().decode()[:-2]  # -2: 文字列に改行コードが含まれるため，それ以外を抜き出す．            
        else:
            return self.is_last_command_success
    
    def get_position(self, axis: Union[int, str]) -> Union[int, Sequence[int]]:
        if axis in [1, "1"]:
            return self.get_status1()[0]
        elif axis in [2, "2"]:
            return self.get_status1()[1]
        else:
            return self.get_status1()[:2]

    @property
    def position1(self) -> int:
        return self.get_position(axis=1)
    
    @property
    def position2(self) -> int:
        return self.get_position(axis=2)

    @property
    def ack1(self) -> str:
        """
        ACK1:  X  コマンドエラー
               K  コマンド正常受付
        """
        return self.get_status1()[2]

    @property
    def ack2(self) -> str:
        """
        ACK2:  L  1 軸目リミットセンサで停止
               M  2 軸目リミットセンサで停止
               W  1、2 軸目共にリミットセンサで停止
               K  正常停止
        """
        return self.get_status1()[3]

    @property
    def ack3(self) -> str:
        """
        ACK3:  B  Busy 状態    L、Q、! コマンドのみ受付可能
               R  Ready 状態   全コマンド受付可能
        """
        return self.get_status1()[4]

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

    def return_origin(self, direction: Union[str, Sequence[str]], axis: Union[int, str]) -> bool:
        """H コマンド(機械原点復帰命令)

        ステージにある機械原点を検出し、その位置を原点とします。
        機械原点を検出後に座標値は 0 となります。
        移動速度は最小速度(S)500PPS、最大速度(F)5000PPS、加減速時間(R) 200mS の固定速度にて動作します。
        原点復帰有効軸は DIP スイッチ設定によります。
        
        ・コマンド形式
          H:1+      1 軸の+側機械原点復帰実施
          H:1-      1 軸の-側機械原点復帰実施
          H:2+      2 軸の+側機械原点復帰実施
          H:2-      2 軸の-側機械原点復帰実施
          H:W++     1 軸+側、2 軸+側の機械原点復帰動作実施
          H:W+-     1 軸+側、2 軸-側の機械原点復帰動作実施
          H:W-+     1 軸-側、2 軸+側の機械原点復帰動作実施
          H:W--     1 軸-側、2 軸-側の機械原点復帰動作実施

        Examples
        --------
        >>> return_origin("+", axis=1)
        >>> return_origin("-", axis=1)
        >>> return_origin("+", axis=2)
        >>> return_origin("-", axis=2)
        >>> return_origin(("+", "+"), axis="W")
        >>> return_origin(("+", "-"), axis="W")
        >>> return_origin(("-", "+"), axis="W")
        >>> return_origin(("-", "-"), axis="W")
        """
        if axis in [1, 2, "1", "2"]:
            if direction in ["+", "-"]:
                n = int(axis)
                m = direction
                return self.raw_command(f"H:{n}{m}")
            else:
                msg = f'"{direction}" is not supported, choose direction from "+" or "-"'
                raise ValueError(msg)
        elif axis == "W":
            if len(direction) == 2:
                if all([d in ["+", "-"] for d in direction]):
                    n = axis
                    m1 = direction[0]
                    m2 = direction[1]
                    return self.raw_command(f"H:{n}{m1}{m2}")
                else:
                    msg = f'"{direction}" is not supported, direction contain "+" or "-"'
                    raise ValueError(msg)
            else:
                msg = f'"Length of `direction` must be 2 (i.e. len(direction) is 2)'
                raise ValueError(msg)
        else:
            msg = f'"{axis}" is not supported, choose axis from [1, 2, "W"]'
            raise ValueError(msg)
        
    def set_relative_pulse(self, pulse: Union[int, Sequence[int]], axis: Union[int, str]) -> bool:
        """M コマンド(相対移動パルス数設定命令)

        移動軸、移動方向、相対移動量を設定する命令です。
        この命令を実行した後には、必ず駆動命令“G”コマンドが必要です。
        移動は加減速駆動となります。
        
        ・コマンド形式
          M:nmPx
        
        ・パラメータ
          n:1又は2又はW　　  1 の時1 軸目動作設定、2 の時2 軸目動作設定、Wにて1、2 軸両軸設定
          m:+又は-        　+にて+方向設定、-にて-方向設定
          x:移動パルス数     0 ~ 16,777,215 の値が設定可能
          
        例) M:W+P500-P200  1 軸目+方向に 500 パルス、2 軸目-方向に 200 パルス移動設定
        　  G              駆動開始

        Examples
        --------
        >>> set_relative_pulse((500, -200), axis="W")
        """
        if axis in [1, 2, "1", "2"]:
            n = int(axis)
            m = "+" if pulse >= 0 else "-"
            x = str(abs(pulse))
            return self.raw_command(f"M:{n}{m}P{x}")
        elif axis == "W":
            if len(pulse) == 2:
                n = axis
                m1 = "+" if pulse[0] >= 0 else "-"
                x1 = str(abs(pulse[0]))
                m2 = "+" if pulse[1] >= 0 else "-"
                x2 = str(abs(pulse[1]))
                return self.raw_command(f"M:{n}{m1}P{x1}{m2}P{x2}")
            else:
                msg = f'"Length of `direction` must be 2 (i.e. len(direction) is 2)'
                raise ValueError(msg)
        else:
            msg = f'"{axis}" is not supported, choose axis from [1, 2, "W"]'
            raise ValueError(msg)

    def jog(self, direction: Union[str, Sequence[str]], axis: Union[int, str]) -> bool:
        """J コマンド(ジョグ運転命令)

        ステージを最小速度(S)にて連続して駆動する命令です。
        この命令を実行した後には、必ず 駆動命令“G”コマンドが必要です。
        移動は S 速度での定速駆動となります。停止させる場合は、L コマンド(停止命令)にて停止をします。
        (L コマンドが無い場合は、リミットセンサまで移動してリミットセンサにて停止します。)

        ・コマンド形式
          J:nm

        ・パラメータ
          n:1又は2又はW     1 の時 1 軸目動作設定、2 の時 2 軸目動作設定、W にて 1、2 軸両軸設定
          m:+又は-　　      +にて+方向設定、-にて-方向設定(n が W 設定の場合 m は 2 つ分設定必要)

        例) J:W-+     1 軸目-方向に 2 軸目+方向に移動設定
        　  G         駆動開始

        Examples
        --------
        >>> jpg(("+", "-"), axis="W")
        """
        if axis in [1, 2, "1", "2"]:
            if direction in ["+", "-"]:
                n = int(axis)
                m = direction
                return self.raw_command(f"J:{n}{m}")
            else:
                msg = f'"{direction}" is not supported, choose direction from "+" or "-"'
                raise ValueError(msg)
        elif axis == "W":
            if len(direction) == 2:
                if all([d in ["+", "-"] for d in direction]):
                    n = axis
                    m1 = direction[0]
                    m2 = direction[1]
                    return self.raw_command(f"J:{n}{m1}{m2}")
                else:
                    msg = f'"{direction}" is not supported, direction contain "+" or "-"'
                    raise ValueError(msg)
            else:
                msg = f'"Length of `direction` must be 2 (i.e. len(direction) is 2)'
                raise ValueError(msg)
        else:
            msg = f'"{axis}" is not supported, choose axis from [1, 2, "W"]'
            raise ValueError(msg)

    def driving(self) -> bool:
        """G コマンド(駆動命令)

        本コマンドにてステージは移動を開始します。
        M、J コマンドの後に本コマンドが必要です。 
        G コマンドのみ“:”が不要です。
        
        ・コマンド形式
          G     駆動開始
        """
        return self.raw_command("G")

    def decelerate_stop(self, axis: Union[int, str]) -> bool:
        """L コマンド(減速停止命令)

        ステージを減速停止させます。

        ・コマンド形式
          L:1     1 軸目減速停止
          L:2     2 軸目減速停止
          L:W     1、2 軸減速停止

        (注)  H:W実行時はL:1、L:2を指定してもステージは停止しません。
              L:W又はL:Eコマンドにて停止指定してください。
        """
        return self.raw_command(f"L:{axis}")

    def immediate_stop(self) -> bool:
        """L:E コマンド(即停止命令)

        ・コマンド形式
          L:E     1、2 軸共に即停止実施
        """
        return self.raw_command("L:E")

    def set_logical_zero(self, axis: Union[int, str]) -> bool:
        """R コマンド(論理原点設定命令)

        停止している場所を座標原点に設定します。
        電源投入時は、その場所が原点(“0”座標値) となります。
        本コマンドを実行すると座標値は“0”となります。

        ・コマンド形式
          R:1     1 軸の論理原点を設定実施 
          R:2     2 軸の論理原点を設定実施 
          R:W     1、2 軸の論理原点を設定実施
        """
        return self.raw_command(f"R:{axis}")

    def set_speed(self, spd_range: int, spd_min: Sequence[int], spd_max: Sequence[int], acceleration_time: Sequence[int]) -> bool:
        """D コマンド(速度設定命令)

        移動速度を変更する命令です。
        電源投入時には、最小速度(S)500PPS、最大速度(F) 5000PPS、加減速時間(R)200mS が設定されています。

        ・コマンド形式
          D:rSspd11Fspd21Rspd31Sspd12Fspd22Rspd32

        ・パラメータ
          r:速度設定レンジ           1:Low Speed Range 2:High Speed Range
          spd1:最小速度(S)設定　     設定範囲:1~ 200PPS(Low Range)50 ~ 20000PPS(High Range)
          spd2:最大速度(F)設定　     設定範囲:1~ 200PPS(Low Range)50 ~ 20000PPS(High Range)
          spd3:加減速時間(R)設定     設定範囲:0 ~1000mS(Low Range/High Range 共通)
          (注)  最小速度Sは最大速度Fより小さい値に設定してください。
                最小速度 S= 最大速度 F、加減速時間 R=0 の場合、理論上加減速を行わず一定速度での駆動になります。
          
        例) D:2S100F1000R200S100F1000R200
             1 軸目の移動速度 S100(PPS), F1000(PPS), R200(mS)、2 軸目の移動速度 S100(PPS), F1000(PPS), R200(mS)に設定します。
        
        Examples
        --------
        >>> set_speed(2, (100, 100), (200, 1000), (1000, 200))
        """
        if type(spd_min) == int:
            spd_min = (spd_min, spd_min)

        if type(spd_max) == int:
            spd_max = (spd_max, spd_max)

        if type(acceleration_time) == int:
            acceleration_time = (acceleration_time, acceleration_time)

        r = spd_range
        spd11, spd12 = spd_min
        spd21, spd22 = spd_max
        spd31, spd32 = acceleration_time
        return self.raw_command(f"D:{r}S{spd11}F{spd21}R{spd31}S{spd12}F{spd22}R{spd32}")

    def energize_motor(self, energize: Union[bool, Sequence[bool]], axis: Union[int, str]) -> bool:
        """C コマンド(励磁 ON/OFF 命令)

        モータを励磁又は、励磁を解除する命令です。

        ・コマンド形式
          C:nm

        ・パラメータ
          n:1又は2又はW     1の時1軸目、2の時2軸目、Wにて1、2軸両軸設定 
          m:0 又は 1        0 にて励磁 OFF、1 にて励磁 ON
          
        例) C:10     1 軸目のモータを励磁 OFF に設定

        Examples
        --------
        >>> energize_motor(False, axis=1)
        """
        if axis in [1, 2, "1", "2"]:
            n = int(axis)
            m = 1 if energize else 0
            return self.raw_command("C:{n}{m}")
        elif axis == "W":
            if len(energize) == 2:
                n = axis
                m1 = 1 if energize[0] else 0
                m2 = 1 if energize[0] else 0
                return self.raw_command(f"C:{n}{m1}{m2}")
            else:
                msg = f'"Length of `direction` must be 2 (i.e. len(direction) is 2)'
                raise ValueError(msg)
        else:
            msg = f'"{axis}" is not supported, choose axis from [1, 2, "W"]'
            raise ValueError(msg)
        
    def get_status1(self) -> Tuple[int, int, str, str, str]:
        """Q コマンド(ステータス確認 1 命令)

        コントローラからステージ動作状況や各軸の座標値等を返送します。

        ・コマンド形式
          Q:
          返送データ  -  1000、-  20000、ACK1、ACK2、ACK3 
                   1 軸座標値 2 軸座標値
                        ACK1:  X  コマンドエラー
                               K  コマンド正常受付
                        ACK2:  L  1 軸目リミットセンサで停止
                               M  2 軸目リミットセンサで停止
                               W  1、2 軸目共にリミットセンサで停止
                               K  正常停止
                        ACK3:  B  Busy 状態    L、Q、! コマンドのみ受付可能
                               R  Ready 状態   全コマンド受付可能
        *)返送データの座標値は符号を含めて 10 桁固定です。(符号左詰め、座標値右詰め)
        """
        status = self.raw_command("Q:").split(",")
        position1 = int(status[0].replace(" ", ""))
        position2 = int(status[1].replace(" ", ""))
        ack1 = status[2]
        ack2 = status[3]
        ack3 = status[4]
        return position1, position2, ack1, ack2, ack3

    def get_status2(self) -> str:
        """! コマンド(ステータス確認 2 命令)

        本機から ACK3 の状況(ステージ移動状況)を返送します。

        ・コマンド形式
          !:
        
        返送データ) 
          B  Busy 状態   L、Q、! コマンドのみ受付可能
          R  Ready 状態  全コマンド受付可能
        """
        return self.raw_command("!:")

    def get_version(self) -> str:
        """? コマンド(内部情報取得命令)

        コントローラの ROM バージョン情報を返送します。

        ・コマンド形式
          ?:V

        返送データ)  
          V2.00  ROM バージョン Ver2.00
        """
        return self.raw_command("?:V")