"""Simulation engine for CORTEX.

This module performs scenario-driven simulations and returns richer
engineering reports for robot systems, markets, epidemics, flight,
and general modeling.
"""

import re
from typing import Dict, Optional

from engineering.robotics import RobotSpecs, RobotSimulator


class SimulationEngine:
    """Performs structured scenario simulations and returns report text."""

    ROBOT_TERMS = (
        "robot",
        "motor",
        "wheel",
        "battery",
        "payload",
        "torque",
        "drive",
        "speed",
        "gear",
    )
    MARKET_TERMS = (
        "market",
        "economy",
        "price",
        "demand",
        "supply",
        "competition",
        "growth",
    )
    EPIDEMIC_TERMS = (
        "disease",
        "epidemic",
        "virus",
        "infection",
        "transmission",
        "spread",
        "recovery",
    )
    FLIGHT_TERMS = (
        "flight",
        "airplane",
        "rocket",
        "trajectory",
        "drone",
        "lift",
        "drag",
        "thrust",
        "wing",
    )
    THERMAL_TERMS = (
        "thermal",
        "heat",
        "temperature",
        "cooling",
        "insulation",
        "heat transfer",
        "conduction",
    )

    def run_simulation(self, request: Optional[str] = "") -> str:
        """Run either a default robot simulation or a scenario-specific simulation."""
        request = (request or "").strip()
        if not request:
            return self._simulate_default_robot()

        request_lower = request.lower()
        if any(term in request_lower for term in self.ROBOT_TERMS):
            return self._simulate_robot_from_request(request)
        if any(term in request_lower for term in self.MARKET_TERMS):
            return self._simulate_market(request)
        if any(term in request_lower for term in self.EPIDEMIC_TERMS):
            return self._simulate_epidemic(request)
        if any(term in request_lower for term in self.FLIGHT_TERMS):
            return self._simulate_flight(request)
        if any(term in request_lower for term in self.THERMAL_TERMS):
            return self._simulate_thermal(request)

        return self._simulate_conceptual(request)

    def _parse_robot_params(self, request: str) -> Dict[str, float]:
        patterns = {
            "mass_kg": r"(\d+(?:\.\d+)?)\s*(?:kg|kilograms)",
            "height_m": r"(\d+(?:\.\d+)?)\s*(?:m|meters|meter)",
            "wheel_radius_m": r"(\d+(?:\.\d+)?)\s*(?:wheel radius|wheel|radius)\s*(?:m|meters|meter)",
            "motor_count": r"(\d+)\s*(?:motors|motor)\b",
            "motor_torque_nm": r"(\d+(?:\.\d+)?)\s*(?:nm|Nm|newton\s*meter|newton meters)",
            "battery_voltage_v": r"(\d+(?:\.\d+)?)\s*(?:v|volts|volt)\b",
            "battery_capacity_ah": r"(\d+(?:\.\d+)?)\s*(?:ah|amp(?:ere)?\s*hours|amp hours)",
            "payload_kg": r"(\d+(?:\.\d+)?)\s*(?:kg|kilograms)\s*(?:payload)?",
            "gear_ratio": r"(\d+(?:\.\d+)?)\s*(?:gear ratio|ratio)\b",
            "motor_speed_rpm": r"(\d+(?:\.\d+)?)\s*(?:rpm|revolutions per minute)",
        }
        values: Dict[str, float] = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, request, re.IGNORECASE)
            if match:
                values[key] = float(match.group(1))
        return values

    def _simulate_default_robot(self) -> str:
        specs = RobotSpecs(
            mass_kg=18.0,
            height_m=0.85,
            wheel_radius_m=0.12,
            motor_count=2,
            motor_torque_nm=25.0,
            battery_voltage_v=24.0,
            battery_capacity_ah=10.0,
            payload_kg=4.0,
            gear_ratio=8.0,
            material="aluminium",
            motor_speed_rpm=4000.0,
        )
        simulator = RobotSimulator(specs)
        problems = simulator.validate()
        if problems:
            report_lines = ["Simulation validation failed:"]
            report_lines.extend(f"- {problem}" for problem in problems)
            return "\n".join(report_lines)

        result = simulator.run()
        return simulator.build_report(result)

    def _simulate_robot_from_request(self, request: str) -> str:
        params = self._parse_robot_params(request)
        specs = RobotSpecs(
            mass_kg=params.get("mass_kg", 18.0),
            height_m=params.get("height_m", 0.85),
            wheel_radius_m=params.get("wheel_radius_m", 0.12),
            motor_count=int(params.get("motor_count", 2)),
            motor_torque_nm=params.get("motor_torque_nm", 25.0),
            battery_voltage_v=params.get("battery_voltage_v", 24.0),
            battery_capacity_ah=params.get("battery_capacity_ah", 10.0),
            payload_kg=params.get("payload_kg", 4.0),
            gear_ratio=params.get("gear_ratio", 8.0),
            material="aluminium",
            motor_speed_rpm=params.get("motor_speed_rpm", 4000.0),
        )
        simulator = RobotSimulator(specs)
        problems = simulator.validate()
        if problems:
            report_lines = ["Robot Simulation validation failed:"]
            report_lines.extend(f"- {problem}" for problem in problems)
            return "\n".join(report_lines)

        result = simulator.run()
        report = simulator.build_report(result)
        return (
            "Robot Simulation Complete\n"
            f"Scenario: {request.strip()}\n\n"
            f"{report}"
        )

    def _simulate_market(self, request: str) -> str:
        request_lower = request.lower()
        price = 100.0
        demand = 1200.0
        supply = 1100.0
        commentary = []

        if "lower price" in request_lower or "discount" in request_lower:
            price *= 0.85
            demand *= 1.25
            supply *= 0.95
            commentary.append("Lower price increases demand but tightens supply.")
        elif "raise price" in request_lower or "higher price" in request_lower:
            price *= 1.15
            demand *= 0.82
            supply *= 1.05
            commentary.append("Higher price improves margin but reduces demand.")
        elif "high demand" in request_lower or "surge" in request_lower:
            demand *= 1.4
            supply *= 1.1
            commentary.append("Demand surge causes inventory pressure.")
        elif "competition" in request_lower:
            supply *= 1.2
            demand *= 0.95
            commentary.append("Competition increases available supply and moderates pricing.")
        else:
            commentary.append("Standard market balance assumptions were used.")

        if demand > supply:
            equilibrium = "Demand exceeds supply; prices are likely to rise."
        elif supply > demand:
            equilibrium = "Supply exceeds demand; prices may soften."
        else:
            equilibrium = "Market appears balanced under current assumptions."

        lines = [
            "Market Simulation Complete",
            "",
            f"Scenario: {request.strip()}",
            "",
            f"Estimated Price.........${price:.2f}",
            f"Estimated Demand........{demand:.0f} units",
            f"Estimated Supply........{supply:.0f} units",
            "",
            equilibrium,
        ]
        lines.extend(f"- {item}" for item in commentary)
        lines.append("\nRecommendation: Review price elasticity, inventory, and marketing before committing.")
        return "\n".join(lines)

    def _simulate_epidemic(self, request: str) -> str:
        request_lower = request.lower()
        population = 10000
        active = 20
        recovered = 0
        r0 = 1.7
        recovery_days = 10
        mitigation = []

        if "vaccine" in request_lower or "vaccinated" in request_lower:
            r0 *= 0.7
            mitigation.append("Vaccination reduces effective transmission.")
        if "mask" in request_lower or "distancing" in request_lower or "quarantine" in request_lower:
            r0 *= 0.75
            mitigation.append("Non-pharmaceutical interventions slow spread.")

        susceptible = population - active - recovered
        days = 30
        for _ in range(days):
            new_cases = min(susceptible, int(active * (r0 / recovery_days)))
            recovered_cases = int(active / recovery_days)
            susceptible -= new_cases
            active += new_cases - recovered_cases
            recovered += recovered_cases
            if active < 0:
                active = 0

        attack_rate = (population - susceptible) / population * 100.0
        lines = [
            "Epidemic Simulation Complete",
            "",
            f"Scenario: {request.strip()}",
            "",
            f"Population..............{population}",
            f"Active Cases............{active}",
            f"Recovered Cases.........{recovered}",
            f"Susceptible Remaining...{susceptible}",
            f"Estimated R₀............{r0:.2f}",
            f"Attack Rate.............{attack_rate:.1f}%",
        ]
        if mitigation:
            lines.append("")
            lines.extend(f"- {item}" for item in mitigation)
        lines.append("\nRecommendation: Reduce R₀ below 1.0 with vaccination, masking, or distancing to control spread.")
        return "\n".join(lines)

    def _simulate_flight(self, request: str) -> str:
        request_lower = request.lower()
        wing_area = 12.0
        mass = 1200.0
        speed = 40.0
        cl = 1.1
        drag_coefficient = 0.035
        air_density = 1.225

        lift = 0.5 * air_density * cl * wing_area * speed ** 2
        drag = 0.5 * air_density * drag_coefficient * wing_area * speed ** 2
        weight = mass * 9.81
        thrust = drag
        climb_margin = lift - weight

        lines = [
            "Flight Simulation Complete",
            "",
            f"Scenario: {request.strip()}",
            "",
            f"Estimated Lift............{lift:.0f} N",
            f"Estimated Drag............{drag:.0f} N",
            f"Aircraft Weight...........{weight:.0f} N",
            f"Required Thrust...........{thrust:.0f} N",
            f"Lift Margin...............{climb_margin:.0f} N",
        ]
        if climb_margin > 0:
            lines.append("\nConclusion: The wing generates enough lift at this speed for level flight.")
        else:
            lines.append("\nConclusion: The current configuration requires more lift or lower weight for sustained flight.")
        lines.append("Recommendation: Adjust wing area, lift coefficient, or cruise speed to improve stability.")
        return "\n".join(lines)

    def _simulate_thermal(self, request: str) -> str:
        request_lower = request.lower()
        temperature_drop = 15.0
        insulation_quality = "moderate"
        if "good insulation" in request_lower or "well insulated" in request_lower:
            temperature_drop = 8.0
            insulation_quality = "good"
        elif "poor insulation" in request_lower or "uninsulated" in request_lower:
            temperature_drop = 22.0
            insulation_quality = "poor"

        lines = [
            "Thermal Simulation Complete",
            "",
            f"Scenario: {request.strip()}",
            "",
            f"Assumed Insulation......{insulation_quality}",
            f"Estimated Temperature Drop...{temperature_drop:.1f} °C over one hour",
            "",
            "Conclusion: Heat transfer is significant unless insulation is improved.",
            "Recommendation: Use better insulation or active cooling to stabilize temperature.",
        ]
        return "\n".join(lines)

    def _simulate_conceptual(self, request: str) -> str:
        return (
            "Simulation Planning Report\n"
            f"Scenario: {request.strip()}\n\n"
            "1. Identify the key variables in the scenario.\n"
            "2. Define the relationships between inputs and outputs.\n"
            "3. Estimate the initial conditions, boundary conditions, and assumptions.\n"
            "4. Select a simple model first, then refine with more detail.\n\n"
            "Recommendation: Use scenario-specific models for best results, then compare multiple outcomes."
        )
