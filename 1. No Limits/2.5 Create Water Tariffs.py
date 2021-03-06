import pandas as pd
import wntr
import wntr.network.controls as controls
import matplotlib.pyplot as plt

#####################
##### FUNCTIONS #####

### returns a dataframe with energy consumption and cost ###


def energy_cost(wn, results, Ta):
    pump_flowrate = results.link['flowrate'].loc[:, wn.pump_name_list]
    head = results.node['head']
    df = wntr.metrics.pump_energy(pump_flowrate, head, wn)
    df["Energy (kWh)"] = df.sum(axis=1)
    df["tariff ($/KWh)"] = Ta
    df['Cost'] = df["tariff ($/KWh)"] * df["Energy (kWh)"]
    df = df.round(2)
    return df

#########################
##### PREREQUISITES #####


### Design Elasticities & Tariff ###
Tariff = pd.read_excel('Tariff.xlsx', index_col=0)
water_tariff = pd.DataFrame(index=Tariff.index, columns=Tariff.columns)

### importing water network model ###
inp_file = 'Net3.inp'
wn = wntr.network.WaterNetworkModel(inp_file)

### Setting Simulation Options ###
wn.options.time.hydraulic_timestep = 3600
wn.options.time.duration = 82800
wn.options.time.report_timestep = 3600
wn.options.energy.global_efficiency = 75

### Removing Controls and Isolating Tanks ###
for control in wn.control_name_list:
    wn.remove_control(control)
wn.get_link('20').status = 'closed'
wn.get_link('40').status = 'closed'
wn.get_link('50').status = 'closed'
wn.get_link('330').status = 'open'
wn.get_link('10').status = 'open'
pump = wn.get_link('10')
act2 = controls.ControlAction(pump, 'status', 1)
cond2 = controls.SimTimeCondition(wn, '=', '0:00:00')
ctrl2 = controls.Control(cond2, act2, name='control2')
wn.add_control('NewTimeControl', ctrl2)

#############################################
### Looping over each scenario of Tariffs ###

for T in Tariff.columns:

    ### Simulation ###
    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()

    ### Calculating Energy and Cost ###
    pump_energy_original = energy_cost(wn, results, Tariff[T])
    sorted_df = pump_energy_original.sort_values(
        ["tariff ($/KWh)", "Cost"], ascending=True)

    ### Creating Water Tariff ###
    df_half = sorted_df["Cost"].iloc[:4]
    half_hours = df_half.index.tolist()

    df_3quarts = sorted_df["Cost"].iloc[4:8]
    quarts_hours = df_3quarts.index.tolist()

    df_1andhalf = sorted_df["Cost"].iloc[len(sorted_df)-8:len(sorted_df)-4]
    overhalf_hours = df_1andhalf.index.tolist()

    df_1andquart = sorted_df["Cost"].iloc[len(sorted_df)-4:len(sorted_df)]
    overquart_hours = df_1andquart.index.tolist()

    for hour in water_tariff.index:

        if hour in half_hours:
            water_tariff.at[hour, T] = 0.5
        elif hour in quarts_hours:
            water_tariff.at[hour, T] = 0.75
        elif hour in overhalf_hours:
            water_tariff.at[hour, T] = 1.5
        elif hour in overquart_hours:
            water_tariff.at[hour, T] = 1.25
        else:
            water_tariff.at[hour, T] = 1

water_tariff.to_excel(
    r'3 Our Tariff Results/0.Water Tariffs.xlsx', header=True)

################
### PLOTTING ###
################

plt.style.use('seaborn')
plt.rc('xtick', labelsize=40)
plt.rc('ytick', labelsize=40)
plt.rc('legend', fontsize=30)


Water_Tariff = pd.read_excel(
    r'3 Our Tariff Results/0.Water Tariffs.xlsx', index_col=0)

index = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
         13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
yticks = [0.5, 0.75, 1, 1.25, 1.5]

Water_Tariff.index = index
hours = [0, 6, 12, 18, 23]


T1 = Water_Tariff.iloc[:, 0:18]
T2 = Water_Tariff.iloc[:, 18:36]
T3 = Water_Tariff.iloc[:, 36:53]


T1.plot(subplots=True, figsize=(15, 50), sharex=True, xticks=hours, grid=True)
plt.savefig('3 Our Tariff Results/Water_Tariff_Plots/T1.png')
T2.plot(subplots=True, figsize=(15, 50), sharex=True, xticks=hours, grid=True)
plt.savefig('3 Our Tariff Results/Water_Tariff_Plots/T2.png')
T3.plot(subplots=True, figsize=(15, 50), sharex=True, xticks=hours, grid=True)
plt.savefig('3 Our Tariff Results/Water_Tariff_Plots/T3.png')


plt.style.use('seaborn')
plt.rc('xtick', labelsize=20)
plt.rc('ytick', labelsize=20)

Water_Tariff = pd.read_excel(
    r'3 Our Tariff Results/0.Water Tariffs.xlsx', index_col=0)
hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
         13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]


for T in Water_Tariff.columns:
    Ta = Water_Tariff[T]
    x = Ta.mean()
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_title('Hourly Water Tariff: '+T, fontdict={'fontsize': 30})
    ax.set_xlabel('time (h)', fontdict={'fontsize': 30})
    ax.set_ylabel('Tariff (factor/GPM)', color='blue',
                  fontdict={'fontsize': 30})
    ax.set_xticks(hours)
    ax.step(hours, Ta.tolist(), where="post",
            color='blue', label='Water Tariff')
    ax.plot(hours, Ta, 'C0o')
    ax.axhline(Ta.mean(), color='red', linestyle='dotted', label='Mean')
    ax.legend(fontsize=20)
    fig.tight_layout()
    plt.savefig('3 Our Tariff Results/Water_Tariff_Plots/' + T + '.png')
    plt.close()
