baseline_co2 = 91.16 #g.CO2/MJ
baseline_m2x = 16 #g.CO2/MJ
p_vlsfo = 615 #EUR/ton

def calculate_penalty(compliance_balance: float, ghg_intensity: float):

    return 2400 * max((compliance_balance, 0)) / (ghg_intensity * 41000)