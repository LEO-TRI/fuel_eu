baseline_co2 = 91.16 #g.CO2/MJ
baseline_m2x = 16 #g.CO2/MJ
p_vlsfo = 615 #EUR/ton

def calculate_penalty(ghg_target_intensity: float, ghg_current_intensity: float, penalty: int=2400):

    compliance_balance = ghg_current_intensity - ghg_target_intensity

    if compliance_balance <= 0:
        return 0

    return (penalty * compliance_balance) / (ghg_current_intensity * 41000)