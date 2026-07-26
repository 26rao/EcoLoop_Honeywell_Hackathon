TOOLS = [
    {
        "name": "set_heating_setpoint",
        "description": "Propose the next heating setpoint in Celsius.",
        "parameters": {"value_c": "float"}
    },
    {
        "name": "set_cooling_setpoint",
        "description": "Propose the next cooling setpoint in Celsius.",
        "parameters": {"value_c": "float"}
    },
    {
        "name": "validate_setpoints",
        "description": "Check proposed setpoints against comfort band and rate-of-change limits before committing.",
        "parameters": {"heating_c": "float", "cooling_c": "float"}
    },
    {
        "name": "parse_energyplus_errors",
        "description": "Read the current run's .err log and return structured severe errors and warnings.",
        "parameters": {}
    }
]
