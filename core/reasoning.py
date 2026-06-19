"""Reasoning engine for CORTEX.

This module is responsible for analysing input data,
validating information, and generating inference summaries.
"""

import re
from typing import Dict, Optional

from core.ai_assistant import AIAdapter
from core.memory import MemoryManager
from core.search import KnowledgeSearch
from core.simulation import SimulationEngine
from engineering.robotics import RobotSimulator, RobotSpecs


class ReasoningEngine:
    """Provides broad local reasoning and optional AI-backed responses."""

    def __init__(self) -> None:
        self.ai = AIAdapter()
        self.knowledge = KnowledgeSearch()
        self.simulation = SimulationEngine()
        self.memory = MemoryManager()
        self.memory.load()

    def analyse(self, data: dict) -> dict:
        """Perform a reasoning pass over provided data."""
        return {
            "status": "READY",
            "summary": "No specific reasoning algorithm implemented yet.",
        }

    def _parse_robot_params(self, request: str) -> dict:
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
        values = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, request, re.IGNORECASE)
            if match:
                values[key] = float(match.group(1))
        return values

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
            report_lines = ["Simulation validation failed:"]
            report_lines.extend(f"- {problem}" for problem in problems)
            return "\n".join(report_lines)
        return simulator.build_report(simulator.run())

    def _local_general_answer(self, request_lower: str, request: str) -> Optional[str]:
        if "remember" in request_lower and "as" in request_lower:
            mirror = request_lower.replace("remember", "", 1).strip()
            key, _, value = mirror.partition(" as ")
            if key and value:
                self.memory.remember(key.strip(), value.strip())
                return f"Memory saved: '{key.strip()}' -> '{value.strip()}'."

        if "what do you remember" in request_lower or "recall" in request_lower:
            query_key = request_lower.replace("what do you remember about", "", 1).replace("recall", "", 1).strip()
            query_key = query_key.strip(" ?.")
            if not query_key:
                return "What would you like me to recall?"
            exact_value = self.memory.recall(query_key)
            if exact_value is not None:
                return f"Memory recall: {query_key} -> {exact_value}"
            matches = self.memory.find_user_memory(query_key)
            if matches:
                lines = ["I found these matching memories:"]
                lines.extend(f"- {k}: {v}" for k, v in matches.items())
                return "\n".join(lines)
            return f"I do not have a stored memory for '{query_key}'."

        if "cup of tea" in request_lower or ("make" in request_lower and "tea" in request_lower):
            return (
                "Analysis Complete.\n"
                "Request: How to make a cup of tea\n"
                "\n"
                "1. Boil clean water.\n"
                "2. Place a tea bag or loose tea in a cup.\n"
                "3. Pour the hot water over the tea.\n"
                "4. Steep for 3 to 5 minutes, depending on tea strength.\n"
                "5. Remove the tea bag or strain the leaves.\n"
                "6. Add milk, sugar, or lemon if desired.\n"
                "\n"
                "Recommendation: Use freshly boiled water and monitor steep time for the desired strength."
            )

        if "solar energy" in request_lower:
            return (
                "Answer Complete.\n"
                "Solar energy is the capture of sunlight and conversion into electricity or heat.\n"
                "Recommendation: Use solar panels or thermal collectors for distributed clean energy systems."
            )

        if "climate change" in request_lower or "global warming" in request_lower:
            return (
                "Analysis Complete.\n"
                "Climate change refers to long-term shifts in temperature and weather patterns, mostly caused by greenhouse gas emissions.\n"
                "Recommendation: Reduce emissions, improve energy efficiency, and support renewable energy solutions."
            )

        if "photosynthesis" in request_lower:
            return (
                "Explanation Complete.\n"
                "Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to create glucose and oxygen.\n"
                "Recommendation: Consider photosynthesis as a model for sustainable energy and carbon capture systems."
            )

        if "computer" in request_lower and ("how" in request_lower or "what" in request_lower or "define" in request_lower):
            return (
                "Answer Complete.\n"
                "A computer is an electronic device that processes data and executes instructions.\n"
                "Recommendation: Use computers for automation, simulation, and data analysis."
            )

        if "programming" in request_lower or "code" in request_lower:
            return (
                "Answer Complete.\n"
                "Programming is the process of writing instructions for computers to perform tasks.\n"
                "Recommendation: Use structured logic, clear naming, and testing when developing software."
            )

        if "python" in request_lower and ("what" in request_lower or "define" in request_lower):
            return (
                "Answer Complete.\n"
                "Python is a high-level programming language known for readability and broad library support.\n"
                "Recommendation: Use Python for automation, data science, and rapid prototyping."
            )

        if "why is the sky blue" in request_lower:
            return (
                "Explanation Complete.\n"
                "The sky appears blue because air molecules scatter shorter blue wavelengths of sunlight more than longer red wavelengths.\n"
                "Recommendation: This is called Rayleigh scattering and is most visible during daytime."
            )

        if ("useful" in request_lower or "should i" in request_lower) and "generative ai" in request_lower:
            return (
                "Answer Complete.\n"
                "Generative AI is a rapidly growing area with strong demand across industries for creating text, images, code, and design ideas.\n"
                "Recommendation: Learning generative AI is useful if you want to work in AI, software engineering, creative tools, or automation. Start with machine learning fundamentals and practical model libraries like Hugging Face or TensorFlow."
            )

        if "who is" in request_lower or "who was" in request_lower or "tell me about" in request_lower:
            if "albert einstein" in request_lower or "einstein" in request_lower:
                return (
                    "Answer Complete.\n"
                    "Albert Einstein was a theoretical physicist known for relativity and contributions to quantum mechanics.\n"
                    "Recommendation: Use Einstein's work when evaluating high-speed or gravitational systems."
                )
            if "isaac newton" in request_lower or "newton" in request_lower:
                return (
                    "Answer Complete.\n"
                    "Isaac Newton was a physicist and mathematician known for classical mechanics and gravity.\n"
                    "Recommendation: Use Newtonian physics for low-speed, non-relativistic engineering."
                )
            if "nikola tesla" in request_lower or ("tesla" in request_lower and "nikola" in request_lower):
                return (
                    "Answer Complete.\n"
                    "Nikola Tesla was an inventor and electrical engineer who advanced alternating current systems.\n"
                    "Recommendation: Reference Tesla when considering electrical power and transmission systems."
                )

        if "machine learning" in request_lower:
            return (
                "Answer Complete.\n"
                "Machine learning is a field of AI focused on training models to identify patterns from data.\n"
                "Recommendation: Use supervised learning for labeled datasets and unsupervised learning for pattern discovery."
            )

        if "robotics" in request_lower:
            return (
                "Answer Complete.\n"
                "Robotics combines mechanics, electronics, and software to build autonomous or semi-autonomous machines.\n"
                "Recommendation: Focus on sensing, control, and power when designing robotic systems."
            )

        if "artificial intelligence" in request_lower or "ai" in request_lower:
            return (
                "Answer Complete.\n"
                "Artificial intelligence enables machines to perform tasks that normally require human intelligence.\n"
                "Recommendation: Use AI for pattern recognition, automation, and decision support, while validating results carefully."
            )

        definitions = {
            "torque": (
                "Definition Complete.\n"
                "Torque is a rotational force applied around an axis.\n"
                "Formula: torque = force × distance (Nm).\n"
                "Recommendation: Use torque when evaluating motor and drivetrain performance."
            ),
            "acceleration": (
                "Definition Complete.\n"
                "Acceleration is the rate of change of velocity over time.\n"
                "Formula: a = Δv / Δt (m/s²).\n"
                "Recommendation: Use acceleration to size motors and estimate motion."
            ),
            "battery": (
                "Definition Complete.\n"
                "A battery stores electrical energy in chemical form.\n"
                "Capacity is measured in ampere-hours (Ah) and energy in watt-hours (Wh).\n"
                "Recommendation: Match battery capacity and voltage to expected system power."
            ),
            "efficiency": (
                "Definition Complete.\n"
                "Efficiency measures the useful output compared to the input.\n"
                "Formula: efficiency = (output / input) × 100%.\n"
                "Recommendation: Use efficiency to compare system performance and losses."
            ),
            "force": (
                "Definition Complete.\n"
                "Force is mass multiplied by acceleration.\n"
                "Formula: F = m × a (N).\n"
                "Recommendation: Use force when sizing motors and analyzing motion."
            ),
            "power": (
                "Definition Complete.\n"
                "Power is the rate at which work is done or energy is transferred.\n"
                "Formula: P = W / t or P = V × I (W).\n"
                "Recommendation: Use power to estimate system energy requirements."
            ),
            "voltage": (
                "Definition Complete.\n"
                "Voltage is the electrical potential difference between two points.\n"
                "Formula: V = I × R (Ohm's law).\n"
                "Recommendation: Use voltage when matching battery and motor requirements."
            ),
            "current": (
                "Definition Complete.\n"
                "Current is the flow of electric charge per unit time.\n"
                "Formula: I = V / R (A).\n"
                "Recommendation: Use current when selecting conductors and fuses."
            ),
            "electricity": (
                "Answer Complete.\n"
                "Electricity is the flow of electric charge through a conductor.\n"
                "Recommendation: Use Ohm's law and power formulas when designing circuits."
            ),
            "internet": (
                "Answer Complete.\n"
                "The Internet is a global network that connects computers and information systems.\n"
                "Recommendation: Use networked systems for remote data access and distributed computing."
            ),
            "gravity": (
                "Answer Complete.\n"
                "Gravity is a force that attracts objects with mass toward each other.\n"
                "Recommendation: Use gravitational calculations for structural loading and orbital motion."
            ),
            "energy": (
                "Answer Complete.\n"
                "Energy is the capacity to do work.\n"
                "Recommendation: Use energy balance and efficiency calculations for system design."
            ),
            "unit": (
                "Answer Complete.\n"
                "I can convert units such as meters to feet, kilograms to pounds, Celsius to Fahrenheit, and more.\n"
                "Recommendation: Ask in the format 'convert 10 meters to feet' or 'what is 5 kg in pounds'."
            ),
        }
        for key, message in definitions.items():
            if key in request_lower:
                return message

        if "convert" in request_lower:
            conversion = self._unit_conversion(request)
            if conversion:
                return conversion

        return None

    def _unit_conversion(self, request: str) -> Optional[str]:
        conversion_map = [
            (r"(\d+(?:\.\d+)?)\s*meters?\s*to\s*feet?", 3.28084, "m", "ft"),
            (r"(\d+(?:\.\d+)?)\s*feet?\s*to\s*meters?", 0.3048, "ft", "m"),
            (r"(\d+(?:\.\d+)?)\s*kilograms?\s*to\s*pounds?", 2.20462, "kg", "lb"),
            (r"(\d+(?:\.\d+)?)\s*pounds?\s*to\s*kilograms?", 0.453592, "lb", "kg"),
            (r"(\d+(?:\.\d+)?)\s*celsius?\s*to\s*fahrenheit?", None, "°C", "°F"),
            (r"(\d+(?:\.\d+)?)\s*fahrenheit?\s*to\s*celsius?", None, "°F", "°C"),
        ]
        for pattern, factor, source_unit, target_unit in conversion_map:
            match = re.search(pattern, request, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if source_unit == "°C":
                    converted = value * 9.0 / 5.0 + 32.0
                elif source_unit == "°F":
                    converted = (value - 32.0) * 5.0 / 9.0
                else:
                    converted = value * factor
                return (
                    f"Conversion Complete.\n"
                    f"{value:.3f} {source_unit} = {converted:.3f} {target_unit}.\n"
                    "Recommendation: Verify the units for your engineering context."
                )
        return None

    def _friendly_greeting(self, request_lower: str) -> Optional[str]:
        if any(word in request_lower for word in ("hello", "hi", "hey", "good morning", "good afternoon", "good evening")):
            return (
                "Hey there! I'm CORTEX — your friendly assistant.\n"
                "Ask me anything or tell me what you'd like to simulate."
            )
        if "how are you" in request_lower:
            return (
                "I'm doing great, thanks!\n"
                "Ready to help you with questions, ideas, and simulations."
            )
        if "thank you" in request_lower or "thanks" in request_lower:
            return "You're welcome! Let me know if you'd like help with another question or simulation."
        return None

    def _looks_like_math_expression(self, expression: str) -> bool:
        return bool(re.fullmatch(r"[0-9\.\+\-\*/\(\) %]+", expression.strip()))

    def _extract_math_expression(self, request_lower: str) -> str | None:
        math_keywords = ["calculate", "evaluate"]
        for keyword in math_keywords:
            if request_lower.startswith(keyword):
                expression = request_lower.replace(keyword, "", 1).strip()
                expression = expression.replace(":", "/")
                return expression

        if request_lower.startswith("what is ") or request_lower.startswith("what's ") or request_lower.startswith("whats "):
            expression = request_lower.split(" ", 2)[-1].strip()
            expression = expression.replace(":", "/")
            if self._looks_like_math_expression(expression):
                return expression

        if self._looks_like_math_expression(request_lower.replace(":", "/")):
            return request_lower.replace(":", "/")
        return None

    def _general_simulation(self, request: str) -> str:
        return self.simulation.run_simulation(request)

    def _build_ai_prompt(self, request: str) -> str:
        user_name = self.memory.get_user_name() or "User"
        memory_keys = [key for key in self.memory.keys() if not key.endswith("_cache")]
        memory_summary = (
            "Stored memory keys: " + ", ".join(memory_keys)
            if memory_keys
            else "No stored personal memory available."
        )
        return (
            "You are CORTEX, a professional computational intelligence assistant. "
            "Answer clearly, accurately, and with a calm engineering style. "
            "When appropriate, provide step-by-step guidance, comparisons, and practical recommendations.\n"
            f"User name: {user_name}\n"
            f"{memory_summary}\n"
            f"Question: {request}\n"
            "If the query seeks factual knowledge, prefer concise explanations and cite the source when possible."
        )

    def _query_knowledge(self, request: str) -> Optional[str]:
        return self.knowledge.search(request)

    def _search_wikipedia(self, request: str) -> Optional[str]:
        if not request.strip():
            return None
        return self.knowledge.search(request)

    def answer_request(self, request: str) -> str:
        """Provide a simple answer for a natural language request."""
        request = request.strip()
        request_lower = request.lower()

        if request_lower.startswith("ask:"):
            request = request[4:].strip()
            request_lower = request.lower()

        greeting = self._friendly_greeting(request_lower)
        if greeting:
            return greeting

        if "simulate" in request_lower or "run simulation" in request_lower:
            return self._general_simulation(request)

        math_expression = self._extract_math_expression(request_lower)
        if math_expression:
            try:
                allowed_chars = "0123456789.+-*/() %"
                if all(char in allowed_chars for char in math_expression):
                    result = eval(math_expression, {"__builtins__": {}})
                    return (
                        "Calculation Complete.\n"
                        f"Expression: {math_expression}\n"
                        f"Result: {result}\n"
                        "Recommendation: Verify the expression and units for engineering context."
                    )
            except Exception:
                pass
            return (
                "Calculation request received, but the expression was not valid.\n"
                "Use a simple numeric expression like: calculate 24 + 36 / 2."
            )

        local_answer = self._local_general_answer(request_lower, request)
        if local_answer is not None:
            return local_answer

        if request_lower.startswith("how to") or request_lower.startswith("how do"):
            if "charge" in request_lower and "battery" in request_lower:
                return (
                    "Analysis Complete.\n"
                    "Request: How to charge a battery\n"
                    "\n"
                    "1. Use the charger specified for the battery chemistry.\n"
                    "2. Connect the charger terminals correctly.\n"
                    "3. Start charging at the recommended current.\n"
                    "4. Monitor the battery temperature and voltage.\n"
                    "5. Stop charging when the battery reaches full voltage.\n"
                    "\n"
                    "Recommendation: Always follow manufacturer charging guidelines."
                )
            if "size" in request_lower and "motor" in request_lower:
                return (
                    "Analysis Complete.\n"
                    "Request: How to size a motor\n"
                    "\n"
                    "1. Determine the load torque requirement.\n"
                    "2. Estimate peak and continuous torque.\n"
                    "3. Choose a motor with adequate torque and speed range.\n"
                    "4. Account for safety margin and thermal limits.\n"
                    "5. Validate with the driven mechanism and control system.\n"
                    "\n"
                    "Recommendation: Use the highest continuous torque that fits your package and power budget."
                )

        if "help" in request_lower or request_lower.strip() == "help":
            return (
                "CORTEX support is active.\n"
                "Supported capabilities:\n"
                "- Simulations: simulate robot, market, epidemic, flight, thermal.\n"
                "- Local engineering responses: what is torque, why is the sky blue, how to charge a battery.\n"
                "- Conversions: convert 10 meters to feet, 5 kg to pounds.\n"
                "- Memory: remember X as Y, recall X.\n"
                "- Encyclopedia lookup: wiki <topic> or ask a general question.\n"
                "Try: 'simulate a robot with 3 motors and 12 kg payload' or 'convert 5 kg to pounds'."
            )

        if request_lower.startswith(("wiki ", "wikipedia ", "britannica ")) or "search for" in request_lower:
            query = request
            if request_lower.startswith("wiki "):
                query = request[5:].strip()
            elif request_lower.startswith("wikipedia "):
                query = request[10:].strip()
            elif request_lower.startswith("britannica "):
                query = request[11:].strip()
            elif "search for" in request_lower:
                query = request_lower.split("search for", 1)[-1].strip()

            if query:
                knowledge_answer = self._query_knowledge(query)
                if knowledge_answer:
                    return knowledge_answer

        if self._should_use_wikipedia(request_lower) or "tell me" in request_lower or "what is" in request_lower or "who is" in request_lower:
            knowledge_answer = self._query_knowledge(request)
            if knowledge_answer:
                return knowledge_answer

        if self.ai.provider != "none":
            return self.ai.ask(self._build_ai_prompt(request))

        return (
            f"Request received: {request.strip()}\n"
            "I can answer many general and technical questions locally.\n"
            "Try: 'what is torque', 'calculate 50 + 5', 'how to charge a battery', or 'who is Einstein'.\n"
            "For broader responses, set OLLAMA_URL to enable local Ollama support."
        )

    def _should_use_wikipedia(self, request_lower: str) -> bool:
        keywords = [
            "what is",
            "what are",
            "whats ",
            "what's ",
            "who is",
            "who was",
            "where is",
            "when is",
            "why is",
            "why does",
            "why can",
            "define",
            "explain",
            "what does",
            "how many",
            "how much",
            "how do",
            "how can",
            "tell me about",
            "tell me how",
            "can you",
            "could you",
            "does",
            "is it",
            "are",
            "who invented",
            "when was",
            "what year",
        ]
        return any(keyword in request_lower for keyword in keywords) or request_lower.startswith("wiki ")
