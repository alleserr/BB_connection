from __future__ import annotations

from app.models.snapshot import (
    ATRState,
    FeatureSnapshot,
    FlagSnapshot,
    PriceVsVWAPState,
    RSIState,
    StateSnapshot,
    TrendDirection,
    TrendStrength,
    VolumeState,
)


class FeatureService:
    """Builds boolean features, normalized states, and lightweight flags."""

    def build(self, latest_row: dict, atr_ratio: float | None) -> tuple[FeatureSnapshot, StateSnapshot, FlagSnapshot]:
        price = float(latest_row["close"])
        ema20 = float(latest_row["ema20"])
        ema50 = float(latest_row["ema50"])
        ema200 = float(latest_row["ema200"])
        rsi14 = float(latest_row["rsi14"])
        relative_volume = float(latest_row["relative_volume"])
        distance_to_vwap_pct = float(latest_row["distance_to_vwap_pct"])

        features = FeatureSnapshot(
            price_above_ema20=price > ema20,
            price_above_ema50=price > ema50,
            price_above_ema200=price > ema200,
            ema20_above_ema50=ema20 > ema50,
            ema50_above_ema200=ema50 > ema200,
        )

        trend_direction = self._trend_direction(features)
        trend_strength = self._trend_strength(features, trend_direction)
        rsi_state = self._rsi_state(rsi14)
        atr_state = self._atr_state(atr_ratio)
        volume_state = self._volume_state(relative_volume)
        price_vs_vwap_state = self._price_vs_vwap_state(distance_to_vwap_pct)

        states = StateSnapshot(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            rsi_state=rsi_state,
            atr_state=atr_state,
            volume_state=volume_state,
            price_vs_vwap_state=price_vs_vwap_state,
        )
        flags = self._flags(states)
        return features, states, flags

    @staticmethod
    def _trend_direction(features: FeatureSnapshot) -> TrendDirection:
        if (
            features.price_above_ema20
            and features.price_above_ema50
            and features.price_above_ema200
            and features.ema20_above_ema50
            and features.ema50_above_ema200
        ):
            return TrendDirection.BULLISH

        if (
            not features.price_above_ema20
            and not features.price_above_ema50
            and not features.price_above_ema200
            and not features.ema20_above_ema50
            and not features.ema50_above_ema200
        ):
            return TrendDirection.BEARISH

        return TrendDirection.NEUTRAL

    @staticmethod
    def _trend_strength(features: FeatureSnapshot, direction: TrendDirection) -> TrendStrength:
        alignment = sum(
            [
                features.price_above_ema20,
                features.price_above_ema50,
                features.price_above_ema200,
                features.ema20_above_ema50,
                features.ema50_above_ema200,
            ]
        )
        if direction == TrendDirection.BULLISH:
            if alignment == 5:
                return TrendStrength.STRONG
            if alignment >= 4:
                return TrendStrength.MODERATE
        elif direction == TrendDirection.BEARISH:
            bearish_alignment = 5 - alignment
            if bearish_alignment == 5:
                return TrendStrength.STRONG
            if bearish_alignment >= 4:
                return TrendStrength.MODERATE
        return TrendStrength.WEAK

    @staticmethod
    def _rsi_state(rsi: float) -> RSIState:
        if rsi < 30:
            return RSIState.OVERSOLD
        if rsi < 55:
            return RSIState.NEUTRAL
        if rsi < 70:
            return RSIState.STRONG
        return RSIState.OVERBOUGHT

    @staticmethod
    def _atr_state(atr_ratio: float | None) -> ATRState:
        if atr_ratio is None:
            return ATRState.NORMAL
        if atr_ratio < 0.85:
            return ATRState.LOW
        if atr_ratio > 1.25:
            return ATRState.HIGH
        return ATRState.NORMAL

    @staticmethod
    def _volume_state(relative_volume: float) -> VolumeState:
        if relative_volume < 0.8:
            return VolumeState.LOW
        if relative_volume > 1.2:
            return VolumeState.ELEVATED
        return VolumeState.NORMAL

    @staticmethod
    def _price_vs_vwap_state(distance_to_vwap_pct: float) -> PriceVsVWAPState:
        if distance_to_vwap_pct <= -1.5:
            return PriceVsVWAPState.EXTENDED_BELOW
        if distance_to_vwap_pct < -0.35:
            return PriceVsVWAPState.BELOW
        if distance_to_vwap_pct <= 0.35:
            return PriceVsVWAPState.NEAR
        if distance_to_vwap_pct < 1.5:
            return PriceVsVWAPState.ABOVE
        return PriceVsVWAPState.EXTENDED_ABOVE

    @staticmethod
    def _flags(states: StateSnapshot) -> FlagSnapshot:
        setup_flags: list[str] = []
        risk_flags: list[str] = []

        if (
            states.trend_direction == TrendDirection.BULLISH
            and states.trend_strength in {TrendStrength.MODERATE, TrendStrength.STRONG}
            and states.price_vs_vwap_state in {PriceVsVWAPState.ABOVE, PriceVsVWAPState.NEAR}
            and states.volume_state != VolumeState.LOW
        ):
            setup_flags.append("trend_continuation")

        if (
            states.trend_direction == TrendDirection.BULLISH
            and states.price_vs_vwap_state in {PriceVsVWAPState.NEAR, PriceVsVWAPState.BELOW}
            and states.rsi_state == RSIState.NEUTRAL
        ):
            setup_flags.append("pullback_candidate")

        if (
            states.rsi_state == RSIState.OVERSOLD
            and states.price_vs_vwap_state in {PriceVsVWAPState.BELOW, PriceVsVWAPState.EXTENDED_BELOW}
        ):
            setup_flags.append("oversold_rebound_candidate")

        if (
            states.volume_state == VolumeState.ELEVATED
            and states.trend_strength in {TrendStrength.MODERATE, TrendStrength.STRONG}
        ):
            setup_flags.append("volume_confirmation")

        if states.price_vs_vwap_state in {PriceVsVWAPState.EXTENDED_ABOVE, PriceVsVWAPState.EXTENDED_BELOW}:
            risk_flags.append("overextended")
        if states.rsi_state == RSIState.OVERBOUGHT:
            risk_flags.append("overbought_rsi")
        if states.volume_state == VolumeState.LOW:
            risk_flags.append("low_volume")
        if states.trend_strength == TrendStrength.WEAK:
            risk_flags.append("weak_trend")
        if states.atr_state == ATRState.HIGH:
            risk_flags.append("high_volatility")

        return FlagSnapshot(setup_flags=setup_flags, risk_flags=risk_flags)

