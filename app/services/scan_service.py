from __future__ import annotations

from app.models.snapshot import (
    MarketSnapshot,
    PriceVsVWAPState,
    Priority,
    RSIState,
    ScanResult,
    TrendDirection,
    TrendStrength,
    VolumeState,
)


class WatchlistScoringService:
    """Simple transparent rule-based scoring for the balanced scan mode."""

    def score_snapshot(self, snapshot: MarketSnapshot) -> ScanResult:
        score = 50
        flags: list[str] = []

        if snapshot.states.trend_direction == TrendDirection.BULLISH:
            score += 15
            flags.append("trend_ok")
        elif snapshot.states.trend_direction == TrendDirection.BEARISH:
            score -= 10
            flags.append("bearish_bias")
        else:
            flags.append("neutral_trend")

        if snapshot.states.trend_strength == TrendStrength.STRONG:
            score += 20
            flags.append("strong_trend")
        elif snapshot.states.trend_strength == TrendStrength.MODERATE:
            score += 10
            flags.append("moderate_trend")
        else:
            score -= 10
            flags.append("weak_trend")

        if snapshot.states.rsi_state == RSIState.STRONG:
            score += 10
            flags.append("rsi_supportive")
        elif snapshot.states.rsi_state == RSIState.OVERSOLD:
            score += 4
            flags.append("oversold")
        elif snapshot.states.rsi_state == RSIState.OVERBOUGHT:
            score -= 8
            flags.append("overbought")

        if snapshot.states.volume_state == VolumeState.ELEVATED:
            score += 10
            flags.append("elevated_volume")
        elif snapshot.states.volume_state == VolumeState.LOW:
            score -= 10
            flags.append("low_volume")

        if snapshot.states.price_vs_vwap_state == PriceVsVWAPState.ABOVE:
            score += 8
            flags.append("above_vwap")
        elif snapshot.states.price_vs_vwap_state == PriceVsVWAPState.NEAR:
            score += 5
            flags.append("near_vwap")
        elif snapshot.states.price_vs_vwap_state == PriceVsVWAPState.BELOW:
            score -= 4
            flags.append("below_vwap")
        elif snapshot.states.price_vs_vwap_state == PriceVsVWAPState.EXTENDED_ABOVE:
            score -= 12
            flags.append("overextended")
        elif snapshot.states.price_vs_vwap_state == PriceVsVWAPState.EXTENDED_BELOW:
            score -= 8
            flags.append("extended_below")

        for flag in snapshot.flags.setup_flags:
            if flag == "trend_continuation":
                score += 12
            elif flag == "pullback_candidate":
                score += 8
            elif flag == "oversold_rebound_candidate":
                score += 6
            elif flag == "volume_confirmation":
                score += 6
            flags.append(flag)

        for flag in snapshot.flags.risk_flags:
            if flag == "overextended":
                score -= 10
            elif flag == "overbought_rsi":
                score -= 8
            elif flag == "weak_trend":
                score -= 6
            elif flag == "high_volatility":
                score -= 6
            flags.append(flag)

        score = max(0, min(100, score))
        if score >= 70:
            priority = Priority.HIGH
        elif score >= 45:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW

        unique_flags = list(dict.fromkeys(flags))
        return ScanResult(
            symbol=snapshot.symbol,
            score=score,
            priority=priority,
            flags=unique_flags,
            snapshot=snapshot,
        )
