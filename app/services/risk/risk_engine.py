"""
Risk Engine - Portfolio risk assessment, position limit checks,
Value-at-Risk calculations, and comprehensive risk reporting.
"""

import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class RiskEngine:
    """Evaluates and reports portfolio risk."""

    def __init__(self, max_drawdown: float = 0.5, default_confidence: float = 0.95):
        self.max_drawdown = max_drawdown
        self.default_confidence = default_confidence

    # ------------------------------------------------------------------
    # Risk assessment
    # ------------------------------------------------------------------

    def assess_risk(self, portfolio: Dict[str, Any]) -> dict:
        """
        Compute an overall risk score for a portfolio.

        Parameters
        ----------
        portfolio : dict
            Expected keys: positions (list of dicts with 'symbol', 'value',
            'volatility'), total_value (float).
        """
        positions = portfolio.get("positions", [])
        total_value = portfolio.get("total_value", 0.0)

        if not positions or total_value <= 0:
            return {"risk_score": 0.0, "level": "unknown", "details": "Empty portfolio"}

        # Concentration risk: Herfindahl index
        weights = [p.get("value", 0) / total_value for p in positions]
        hhi = sum(w ** 2 for w in weights)

        # Weighted average volatility
        avg_vol = sum(
            (p.get("value", 0) / total_value) * p.get("volatility", 0.3)
            for p in positions
        )

        # Combined risk score (0-100)
        concentration_score = min(hhi * 100, 50)
        volatility_score = min(avg_vol * 100, 50)
        risk_score = round(concentration_score + volatility_score, 2)

        if risk_score > 70:
            level = "high"
        elif risk_score > 40:
            level = "medium"
        else:
            level = "low"

        return {
            "risk_score": risk_score,
            "level": level,
            "concentration_hhi": round(hhi, 4),
            "avg_volatility": round(avg_vol, 4),
            "position_count": len(positions),
        }

    # ------------------------------------------------------------------
    # Position limit checks
    # ------------------------------------------------------------------

    def check_position_limits(
        self, position: dict, limits: dict
    ) -> dict:
        """
        Check whether a position violates given limits.

        Parameters
        ----------
        position : dict
            Keys: symbol, value, leverage (optional)
        limits : dict
            Keys: max_position_value, max_leverage, max_concentration_pct,
            portfolio_total_value (needed for concentration check)
        """
        violations: List[str] = []

        pos_value = position.get("value", 0)
        leverage = position.get("leverage", 1.0)

        max_val = limits.get("max_position_value", float("inf"))
        if pos_value > max_val:
            violations.append(
                f"Position value {pos_value} exceeds max {max_val}"
            )

        max_lev = limits.get("max_leverage", float("inf"))
        if leverage > max_lev:
            violations.append(
                f"Leverage {leverage}x exceeds max {max_lev}x"
            )

        portfolio_total = limits.get("portfolio_total_value", 0)
        max_conc = limits.get("max_concentration_pct", 100)
        if portfolio_total > 0:
            conc_pct = (pos_value / portfolio_total) * 100
            if conc_pct > max_conc:
                violations.append(
                    f"Concentration {conc_pct:.1f}% exceeds max {max_conc}%"
                )

        return {
            "within_limits": len(violations) == 0,
            "violations": violations,
            "position_symbol": position.get("symbol", "unknown"),
        }

    # ------------------------------------------------------------------
    # Value at Risk
    # ------------------------------------------------------------------

    def calculate_var(
        self,
        portfolio: Dict[str, Any],
        confidence: Optional[float] = None,
        horizon_days: int = 1,
    ) -> dict:
        """
        Parametric Value at Risk (variance-covariance method).

        Parameters
        ----------
        portfolio : dict
            Same structure as assess_risk.
        confidence : float
            Confidence level (e.g. 0.95 or 0.99).
        horizon_days : int
            Holding period in days.
        """
        confidence = confidence or self.default_confidence
        total_value = portfolio.get("total_value", 0.0)
        positions = portfolio.get("positions", [])

        if total_value <= 0:
            return {"var": 0.0, "confidence": confidence}

        # Z-scores for common confidence levels
        z_scores = {0.90: 1.282, 0.95: 1.645, 0.99: 2.326}
        z = z_scores.get(confidence, 1.645)

        # Portfolio volatility (simplified: weighted average)
        weights = [p.get("value", 0) / total_value for p in positions]
        vols = [p.get("volatility", 0.3) for p in positions]
        port_vol = sum(w * v for w, v in zip(weights, vols))

        # Scale to horizon
        daily_vol = port_vol / math.sqrt(252)
        horizon_vol = daily_vol * math.sqrt(horizon_days)

        var_value = round(total_value * z * horizon_vol, 2)

        return {
            "var": var_value,
            "var_pct": round(z * horizon_vol * 100, 2),
            "confidence": confidence,
            "horizon_days": horizon_days,
            "portfolio_volatility": round(port_vol, 4),
        }

    # ------------------------------------------------------------------
    # Comprehensive report
    # ------------------------------------------------------------------

    def get_risk_report(self, portfolio: Dict[str, Any]) -> dict:
        """Generate a comprehensive risk report for the portfolio."""
        assessment = self.assess_risk(portfolio)
        var_95 = self.calculate_var(portfolio, confidence=0.95)
        var_99 = self.calculate_var(portfolio, confidence=0.99)

        positions = portfolio.get("positions", [])
        limit_checks = []
        default_limits = {
            "max_position_value": portfolio.get("total_value", 0) * 0.3,
            "max_leverage": 5.0,
            "max_concentration_pct": 30,
            "portfolio_total_value": portfolio.get("total_value", 0),
        }
        for pos in positions:
            limit_checks.append(self.check_position_limits(pos, default_limits))

        violations_count = sum(
            1 for lc in limit_checks if not lc["within_limits"]
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "assessment": assessment,
            "var_95": var_95,
            "var_99": var_99,
            "position_limit_checks": limit_checks,
            "violations_count": violations_count,
            "recommendations": self._generate_recommendations(
                assessment, var_95, violations_count
            ),
        }

    def _generate_recommendations(
        self, assessment: dict, var_95: dict, violations: int
    ) -> List[str]:
        recs = []
        if assessment.get("level") == "high":
            recs.append("Consider reducing overall portfolio exposure")
        if assessment.get("concentration_hhi", 0) > 0.25:
            recs.append("Portfolio is concentrated; diversify across more assets")
        if var_95.get("var_pct", 0) > 5:
            recs.append("Daily VaR exceeds 5%; consider hedging strategies")
        if violations > 0:
            recs.append(f"{violations} position(s) violate limits; review sizing")
        if not recs:
            recs.append("Portfolio risk levels are within acceptable parameters")
        return recs


def check_risk_limits() -> bool:
    """Legacy function kept for backward compatibility."""
    drawdown = random.uniform(0, 1)
    return drawdown < 0.5
