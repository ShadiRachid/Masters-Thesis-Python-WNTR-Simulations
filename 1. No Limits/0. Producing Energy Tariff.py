import pandas as pd
import wntr
import wntr.network.controls as controls
import random
import matplotlib.pyplot as plt

tariff = pd.DataFrame(index = [0, 3600, 7200, 10800, 14400, 18000, 21600, 
                                     25200, 28800, 32400, 36000, 39600,  43200, 
                                     46800, 50400, 54000, 57600, 61200, 64800, 
                                     68400, 72000, 75600, 79200, 82800])

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

### Simulation ###
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()

### Calculating Energy and Cost ###
pump_flowrate = results.link['flowrate'].loc[:,wn.pump_name_list]
head = results.node['head']
df = wntr.metrics.pump_energy(pump_flowrate, head, wn)
df["Energy (kWh)"] = df.sum(axis=1)
df = df.round(2)
sorted_df = df.sort_values(["Energy (kWh)"],ascending = True) 

### Creating Energy Tariff ### 
df_half = sorted_df["Energy (kWh)"].iloc[:4]
half_hours = df_half.index.tolist()

df_3quarts = sorted_df["Energy (kWh)"].iloc[4:8]
quarts_hours = df_3quarts.index.tolist()

df_1andhalf = sorted_df["Energy (kWh)"].iloc[len(sorted_df)-8:len(sorted_df)-4]
overhalf_hours = df_1andhalf.index.tolist()

df_1andquart = sorted_df["Energy (kWh)"].iloc[len(sorted_df)-4:len(sorted_df)]
overquart_hours = df_1andquart.index.tolist()

for hour in tariff.index:
    tariff.at[hour,'Flat'] = 1

for hour in tariff.index:  
    if hour in half_hours: tariff.at[hour,'Symmetric'] = 0.5
    elif hour in quarts_hours: tariff.at[hour,'Symmetric'] = 0.75
    elif hour in overhalf_hours: tariff.at[hour,'Symmetric'] = 1.5
    elif hour in overquart_hours: tariff.at[hour,'Symmetric'] = 1.25
    else: tariff.at[hour,'Symmetric'] = 1

for hour in tariff.index:
    if hour in half_hours: tariff.at[hour,'Opposite'] = 1.5
    elif hour in quarts_hours: tariff.at[hour,'Opposite'] = 1.25
    elif hour in overhalf_hours: tariff.at[hour,'Opposite'] = 0.5
    elif hour in overquart_hours: tariff.at[hour,'Opposite'] = 0.75
    else: tariff.at[hour,'Opposite'] = 1

random_tariff = tariff['Opposite'].copy().tolist()

i=1
while i<51:
    random.shuffle(random_tariff)
    string = 'Random '+str(i)
    tariff[string] = random_tariff
    i+=1

tariff.to_excel('Tariff.xlsx',header  = True)



### PLOTTING ###

plt.style.use('seaborn')
plt.rc('xtick',labelsize=40)
plt.rc('ytick',labelsize=40)
plt.rc('legend', fontsize=30)


Tariff = pd.read_excel('Tariff.xlsx',index_col=0)

index = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
yticks = [0.5, 0.75, 1, 1.25, 1.5]

Tariff.index = index
hours = [0, 6, 12, 18, 23]


T1 = Tariff.iloc[:,0:18]
T2 = Tariff.iloc[:,18:36]
T3 = Tariff.iloc[:,36:53]


T1.plot(subplots=True, figsize=(15, 50), sharex = True, xticks = hours, grid = True)
plt.savefig('0 Energy Tariff Plots/T1.png')
T2.plot(subplots=True, figsize=(15, 50), sharex = True, xticks = hours, grid = True)
plt.savefig('0 Energy Tariff Plots/T2.png')
T3.plot(subplots=True, figsize=(15, 50), sharex = True, xticks = hours, grid = True)
plt.savefig('0 Energy Tariff Plots/T3.png')


for T in Tariff.columns:
    Ta = Tariff[T]
    x = Ta.mean()
    fig, ax = plt.subplots(figsize=(15,10))
    ax.set_title('Hourly Energy Tariff: '+T,fontdict={'fontsize': 30} )
    ax.set_xlabel('time (h)', fontdict={'fontsize': 30})
    ax.set_ylabel('Tariff (factor/W)', color='blue', fontdict={'fontsize': 30})
    ax.set_xticks(hours)
    ax.set_yticks(yticks)
    ax.step(hours, Ta.tolist(), where = "post", color='blue', label = 'Hourly Values')
    ax.plot(hours,Ta,'C0o')
    ax.axhline(Ta.mean(), color = 'red', linestyle='dotted', label='Mean')
    ax.legend(fontsize = 20)
    fig.tight_layout() 
    plt.savefig('0 Energy Tariff Plots/'+ T +'.png')
    plt.close()