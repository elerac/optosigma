import time
from .gsc01 import GSC01

class PWA100(GSC01):
    # ステージを動かしたときに待つかどうかのフラグ
    is_sleep_until_stop = True

    # 1パルスで移動する角度（固定値）
    degree_per_pulse = 0.06  # [deg/pulse]

    def reset(self):
        ret =  self.return_origin()
        if self.is_sleep_until_stop:
            self.sleep_until_stop()
        return ret

    def stop(self):
        return self.decelerate_stop()

    def sleep_until_stop(self):
        """ステージが停止するまで待つ"""
        while not self.is_ready:
            time.sleep(0.01)

    @property
    def degree(self) -> float:
        """ステージの回転角度[deg]を返す"""
        position = self.get_position()
        degree = self.pos2deg(position)
        return degree
    
    @degree.setter
    def degree(self, target_degree: float):
        """ステージを指定した角度に動かす"""
        current_degree = self.degree
        target_degree %= 360
        relative_degree = (target_degree - current_degree) % 360
        relative_position = self.deg2pos(relative_degree)

        self.set_relative_pulse(relative_position)
        self.driving()
        if self.is_sleep_until_stop:
            self.sleep_until_stop()

    def pos2deg(self, position: int) -> float:
        """ステージ位置から角度[deg]に変換"""
        return (position % (360.0 / self.degree_per_pulse)) * self.degree_per_pulse

    def deg2pos(self, degree: float) -> int:
        """角度[deg]からステージ位置に変換"""
        return int(degree / self.degree_per_pulse)