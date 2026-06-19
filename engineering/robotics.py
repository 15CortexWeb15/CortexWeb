"""Robot engineering module for CORTEX.

Provides structured robot specifications, validation, and simulation calculations.
"""

from dataclasses import dataclass, field
from math import pi
from typing import List, Optional


@dataclass
class RobotSpecs:
    """Robot specification data used for simulation."""

    mass_kg: float
    height_m: float
    wheel_radius_m: float
    motor_count: int
    motor_torque_nm: float
    battery_voltage_v: float
    battery_capacity_ah: float
    payload_kg: float
    gear_ratio: float
    material: str
    motor_speed_rpm: Optional[float] = None
    drag_coefficient: float = 1.1
    frontal_area_m2: float = 0.6
    wheelbase_m: float = 0.4

    def validate(self) -> List[str]:
        """Validate the robot specification values."""
        problems: List[str] = []
        if self.mass_kg <= 0:
            problems.append("Robot mass must be greater than zero.")
        if self.height_m <= 0:
            problems.append("Robot height must be greater than zero.")
        if self.wheel_radius_m <= 0:
            problems.append("Wheel radius must be greater than zero.")
        if self.motor_count <= 0:
            problems.append("Motor count must be at least one.")
        if self.motor_torque_nm <= 0:
            problems.append("Motor torque must be greater than zero.")
        if self.battery_voltage_v <= 0:
            problems.append("Battery voltage must be greater than zero.")
        if self.battery_capacity_ah <= 0:
            problems.append("Battery capacity must be greater than zero.")
        if self.payload_kg < 0:
            problems.append("Payload cannot be negative.")
        if self.gear_ratio <= 0:
            problems.append("Gear ratio must be greater than zero.")
        if self.drag_coefficient <= 0:
            problems.append("Drag coefficient must be greater than zero.")
        if self.frontal_area_m2 <= 0:
            problems.append("Frontal area must be greater than zero.")
        if self.wheelbase_m <= 0:
            problems.append("Wheelbase must be greater than zero.")
        if not self.material:
            problems.append("Material must be specified.")
        if self.motor_speed_rpm is not None and self.motor_speed_rpm <= 0:
            problems.append("Motor speed RPM must be greater than zero when provided.")
        return problems


@dataclass
class RobotSimulationResult:
    """Structured result values for a robot simulation."""

    weight_kg: float
    weight_force_n: float
    total_drive_force_n: float
    total_torque_nm: float
    battery_energy_wh: float
    max_speed_m_s: Optional[float]
    estimated_runtime_h: Optional[float]
    acceleration_m_s2: Optional[float]
    efficiency_pct: float
    stability_assessment: str
    assumptions: List[str] = field(default_factory=list)


class RobotSimulator:
    """Perform robot simulations using engineering calculations."""

    GRAVITY_M_S2 = 9.81
    ROLLING_RESISTANCE_COEFFICIENT = 0.02
    DEFAULT_OPERATING_SPEED_M_S = 1.0
    DEFAULT_SYSTEM_EFFICIENCY = 0.75

    def __init__(self, specs: RobotSpecs) -> None:
        self.specs = specs
        self.assumptions: List[str] = []

    def validate(self) -> List[str]:
        """Return validation problems for the current robot specs."""
        return self.specs.validate()

    def total_mass(self) -> float:
        """Return total robot mass including payload."""
        return self.specs.mass_kg + self.specs.payload_kg

    def weight_force(self) -> float:
        """Return gravitational force in newtons."""
        return self.total_mass() * self.GRAVITY_M_S2

    def total_torque(self) -> float:
        """Return total torque available at the wheel input."""
        return self.specs.motor_torque_nm * self.specs.motor_count * self.specs.gear_ratio

    def total_drive_force(self) -> float:
        """Return the available linear force at the wheel circumference."""
        return self.total_torque() / self.specs.wheel_radius_m

    def required_rolling_force(self) -> float:
        """Estimate rolling resistance force for a flat surface."""
        return self.weight_force() * self.ROLLING_RESISTANCE_COEFFICIENT

    def aerodynamic_drag(self, speed_m_s: float) -> float:
        """Estimate aerodynamic drag force at a given speed."""
        air_density = 1.225
        return 0.5 * air_density * self.specs.drag_coefficient * self.specs.frontal_area_m2 * speed_m_s ** 2

    def battery_energy(self) -> float:
        """Return stored battery energy in watt-hours."""
        return self.specs.battery_voltage_v * self.specs.battery_capacity_ah

    def estimated_runtime(self) -> Optional[float]:
        """Estimate runtime in hours using rolling resistance, drag, and a nominal speed."""
        if self.total_drive_force() <= 0:
            return None
        speed = self.DEFAULT_OPERATING_SPEED_M_S
        rolling_power = self.required_rolling_force() * speed
        drag_power = self.aerodynamic_drag(speed) * speed
        total_power = (rolling_power + drag_power) / self.DEFAULT_SYSTEM_EFFICIENCY
        if total_power <= 0:
            return None
        return self.battery_energy() / total_power

    def max_speed(self) -> Optional[float]:
        """Estimate maximum wheel speed in meters per second when motor RPM is provided."""
        if self.specs.motor_speed_rpm is None:
            self.assumptions.append(
                "Maximum speed not calculated because motor speed RPM was not provided."
            )
            return None
        wheel_rpm = self.specs.motor_speed_rpm / self.specs.gear_ratio
        return wheel_rpm * 2 * pi * self.specs.wheel_radius_m / 60.0

    def acceleration(self) -> Optional[float]:
        """Estimate acceleration from available drive force and total mass."""
        available_force = self.total_drive_force() - self.required_rolling_force()
        if available_force <= 0:
            return None
        return available_force / self.total_mass()

    def efficiency(self) -> float:
        """Estimate efficiency based on available drive force and rolling resistance."""
        required_force = self.required_rolling_force()
        available_force = self.total_drive_force()
        if required_force <= 0:
            return 0.0
        efficiency = min(100.0, max(0.0, available_force / required_force * 100.0))
        return efficiency

    def stability_assessment(self) -> str:
        """Return a brief stability assessment based on geometry and drive force."""
        if self.specs.height_m / (2.0 * self.specs.wheel_radius_m) > 3.0:
            return "High centre of gravity due to tall geometry; stability may be reduced."
        if self.total_drive_force() < self.required_rolling_force():
            return "Drive force is marginal for flat-surface motion."
        roll_over_ratio = self.specs.wheelbase_m / self.specs.height_m
        if roll_over_ratio < 0.5:
            return "Narrow wheelbase relative to height; rollover risk may be elevated."
        return "Configuration appears mechanically viable for level terrain."

    def run(self) -> RobotSimulationResult:
        """Execute the simulation and return a results object."""
        result = RobotSimulationResult(
            weight_kg=self.total_mass(),
            weight_force_n=self.weight_force(),
            total_drive_force_n=self.total_drive_force(),
            total_torque_nm=self.total_torque(),
            battery_energy_wh=self.battery_energy(),
            max_speed_m_s=self.max_speed(),
            estimated_runtime_h=self.estimated_runtime(),
            acceleration_m_s2=self.acceleration(),
            efficiency_pct=self.efficiency(),
            stability_assessment=self.stability_assessment(),
            assumptions=self.assumptions.copy(),
        )
        return result

    def build_report(self, result: RobotSimulationResult) -> str:
        """Format a concise engineering report from result values."""
        lines = [
            "Robot Simulation Complete",
            "",
            f"Weight..................{result.weight_kg:.2f} kg",
            f"Weight Force............{result.weight_force_n:.1f} N",
            f"Total Torque............{result.total_torque_nm:.1f} Nm",
            f"Drive Force.............{result.total_drive_force_n:.1f} N",
            f"Battery Energy..........{result.battery_energy_wh:.1f} Wh",
        ]

        if result.max_speed_m_s is not None:
            lines.append(f"Maximum Speed...........{result.max_speed_m_s:.2f} m/s")
        else:
            lines.append("Maximum Speed...........N/A")

        if result.estimated_runtime_h is not None:
            lines.append(f"Estimated Runtime.......{result.estimated_runtime_h:.2f} h")
        else:
            lines.append("Estimated Runtime.......N/A")

        if result.acceleration_m_s2 is not None:
            lines.append(f"Estimated Acceleration..{result.acceleration_m_s2:.2f} m/s²")
        else:
            lines.append("Estimated Acceleration..N/A")

        lines.extend([
            f"Efficiency..............{result.efficiency_pct:.1f} %",
            f"Stability...............{result.stability_assessment}",
        ])

        if result.assumptions:
            lines.append("")
            lines.append("Assumptions:")
            for assumption in result.assumptions:
                lines.append(f"- {assumption}")

        lines.append("")
        if result.efficiency_pct < 50.0:
            recommendation = "Recommend reviewing motor torque, gear ratio, or reducing payload."
        elif result.acceleration_m_s2 is not None and result.acceleration_m_s2 < 0.5:
            recommendation = "Acceleration is low; consider higher torque, lighter mass, or lower gearing."
        else:
            recommendation = "Configuration is acceptable for light indoor applications."

        lines.append(f"Recommendation..........{recommendation}")
        return "\n".join(lines)
