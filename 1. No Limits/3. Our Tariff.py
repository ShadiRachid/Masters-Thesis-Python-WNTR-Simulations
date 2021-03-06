import numpy as np
import pandas as pd
import wntr
import wntr.network.controls as controls
import random
import matplotlib.pyplot as plt
from matplotlib import cm

#####################
##### FUNCTIONS #####

### Returns all demands at each node and hour ###
def all_demands(wn):
    Index = [0, 3600, 7200, 10800, 14400, 18000, 21600, 25200, 28800, 32400, 36000, 39600, 
             43200, 46800, 50400, 54000, 57600, 61200, 64800, 68400, 72000, 75600, 79200, 82800]
    df= pd.DataFrame(index = Index)
    for name in wn.junction_name_list:
        junction = wn.get_node(name)
        lst = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        for demand in junction.demand_timeseries_list:
            base = demand.base_value
            pat = demand.pattern
            pattern = wn.get_pattern(pat)
            pattern_multipliers = pattern.multipliers
            dvs = base*pattern_multipliers
            lst = np.add(lst,dvs)
        df[name] = lst    
    for col in df.columns:
        if df[col].sum()==0:
            df = df.drop([col],axis =1)         
    return df

### returns dataframe with hourly distribution of total demand in network ###
def total_hourly_demand(wn,Ta):
    df = all_demands(wn)
    df['Total Demands'] = df.sum(axis = 1)
    df["tariff ($/GPH)"] = Ta
    df["Revenue ($)"] = df["tariff ($/GPH)"] * df['Total Demands']
    return df

### returns a dataframe with energy consumption and cost ###
def energy_cost(wn,results,Ta):
    pump_flowrate = results.link['flowrate'].loc[:,wn.pump_name_list]
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
step = 0.05
E = np.arange(step,1+step,step).round(2).tolist() #elasticities 
Tariff = pd.read_excel('Tariff.xlsx',index_col=0)
water_tariff = pd.read_excel(r'3 Our Tariff Results/0.Water Tariffs.xlsx',index_col=0)

### Opening all different results dataframes ##
EE= E.copy().insert(0,0)
energy_savings_percentage = pd.DataFrame(index = EE, columns = Tariff.columns)
cost_savings_percentage = pd.DataFrame(index = EE, columns = Tariff.columns)
revenue_increase_percentage = pd.DataFrame(index = EE, columns = Tariff.columns)
net_increase_percentage = pd.DataFrame(index = EE, columns = Tariff.columns)
total_demand_difference = pd.DataFrame(index = EE, columns = Tariff.columns)
Demand_shifted_percentage = pd.DataFrame(index = EE, columns = Tariff.columns)

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

original_demands_df = all_demands(wn)

########################
### OVERALL ANALYSIS ###
########################

#############################################
### Looping over each scenario of Tariffs ###

for T in Tariff.columns:
    ### Calculating Total Decrease in Tariff for Rebound ###
    RT = 0
    for value in water_tariff[T]:
        if value < water_tariff[T].mean():
            RT += water_tariff[T].mean() - value
            
    ##########################################################################
    ### First Part: WNTR Simulation of Network with Existing Demands (BAU) ### 
    
    ### Simulation ###
    wn.assign_demand(original_demands_df,pattern_prefix = str(random.random()))
    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()
    
    ### Calculating Energy and Cost ###
    pump_energy_original = energy_cost(wn,results,Tariff[T])
    total_hourly_demand_original = total_hourly_demand(wn,water_tariff[T])
    
    original_energy = pump_energy_original['Energy (kWh)'].sum()
    original_cost = pump_energy_original['Cost'].sum()
    original_revenue = total_hourly_demand_original["Revenue ($)"].sum()
    original_net = original_revenue - original_cost
    
    #####################################################################################################
    ### Second Part: WNTR Simulation of Network Under Different Elasticities with New Demand Patterns ###
    
    ### Defining response_details dataframe to track shifted demand ###
    response_details = pd.DataFrame()
    
    ### looping over all elasticity values ### 
    for e in E:
        
        ### producing new demand patterns ###  
        new_demands_df = original_demands_df.copy()
        for demand in new_demands_df.columns:
            QT = 0
            response_details.at[demand,'Demand Before'] = original_demands_df[demand].sum()
            for hour in new_demands_df.index:
                if water_tariff.loc[hour,T] > water_tariff[T].mean():
                    new_demands_df.at[hour,demand] = abs((e)*(water_tariff.loc[hour,T] - water_tariff[T].mean())
                                                         *(original_demands_df.loc[hour,demand]) - original_demands_df.loc[hour,demand])
                    QT += abs(original_demands_df.loc[hour,demand] - new_demands_df.loc[hour,demand])       
            response_details.at[demand,'shifted demand'] = round(QT,3)   
            response_details.at[demand,'% of demand shifted'] = round((QT*100)/original_demands_df[demand].sum(),2)
            
            for hour in new_demands_df.index:
                if water_tariff.loc[hour,T] < water_tariff[T].mean():
                    Delta = (QT/RT)*abs(water_tariff[T].mean() - water_tariff.loc[hour,T])
                    new_demands_df.at[hour,demand] = original_demands_df.loc[hour,demand] + Delta
            response_details.at[demand,'Demand After'] = new_demands_df[demand].sum()
            
        ### Assigning new demands to WDS and checking the success of the operation ###
        wn.assign_demand(new_demands_df,pattern_prefix = str(random.random()))
        altered_demand = all_demands(wn)  
        
        ### Simulation ###
        sim = wntr.sim.EpanetSimulator(wn)
        results_sim = sim.run_sim()
        
        ### Calculating Energy and Cost ###
        pump_energy = energy_cost(wn,results_sim,Tariff[T])
        total_hourly_demand_new = total_hourly_demand(wn,water_tariff[T])
        
        new_energy = pump_energy['Energy (kWh)'].sum()
        new_cost = pump_energy['Cost'].sum()
        new_revenue = total_hourly_demand_new["Revenue ($)"].sum()
        new_net = new_revenue - new_cost
        ###
        energy_savings_percentage.at[e,T] = round((new_energy - original_energy)*100/original_energy ,2)
        cost_savings_percentage.at[e,T] = round((original_cost - new_cost)*100/original_cost,2)
        revenue_increase_percentage.at[e,T] = round((new_revenue - original_revenue)*100/original_revenue,2)
        net_increase_percentage.at[e,T] = round((new_net - original_net)*100/abs(original_net),2)
        total_demand_difference.at[e,T] = round(response_details['Demand Before'].sum() - response_details['Demand After'].sum(),4)
        Demand_shifted_percentage.at[e,T] = round(response_details['shifted demand'].sum() * 100 / response_details['Demand Before'].sum(),2)

water_tariff.to_excel(r'3 Our Tariff Results/0.Water Tariffs.xlsx',header = True)     
energy_savings_percentage.to_excel(r'3 Our Tariff Results/1.Energy Savings Percentage.xlsx',header = True)
cost_savings_percentage.to_excel(r'3 Our Tariff Results/2.Cost Savings Percentage.xlsx',header = True)
revenue_increase_percentage.to_excel(r'3 Our Tariff Results/3.Revenue Increase Percentage.xlsx',header = True)
net_increase_percentage.to_excel(r'3 Our Tariff Results/4.Net Increase Percentage.xlsx',header = True)
total_demand_difference.to_excel(r'3 Our Tariff Results/5.Total Demand Difference.xlsx',header = True)
Demand_shifted_percentage.to_excel(r'3 Our Tariff Results/6.Demand Shifted Percentage.xlsx',header = True)  


#########################
### SPECIFIC ANALYSIS ###
#########################

#########################
##### PREREQUISITES #####

### Design Elasticities & Tariff ###
e = 0.7
Tariff = pd.read_excel('Tariff.xlsx',index_col=0)
water_tariff = pd.read_excel(r'3 Our Tariff Results/0.Water Tariffs.xlsx',index_col=0)
T = 'Symmetric'

### Opening EXCEL WRITERS and TXT FILE##
writer1 = pd.ExcelWriter(r'3 Our Tariff Results/A. Demands.xlsx', engine='xlsxwriter')

hourly_results = pd.DataFrame(index = [0, 3600, 7200, 10800, 14400, 18000, 21600, 25200, 28800, 32400, 36000, 39600, 
                                       43200, 46800, 50400, 54000, 57600, 61200, 64800, 68400, 72000, 75600, 79200, 82800])
summary = pd.DataFrame( index = ['value'])

hourly_results['Energy Tariff'] = Tariff[T]
hourly_results['Water Tariff'] = water_tariff[T]

### Calculating Total Decrease in Tariff for Rebound ###
RT = 0
for value in water_tariff[T]:
    if value < water_tariff[T].mean():
        RT += water_tariff[T].mean() - value

##########################################################################
### First Part: WNTR Simulation of Network with Existing Demands (BAU) ### 

### Simulation ###
wn.assign_demand(original_demands_df,pattern_prefix = str(random.random()))
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()
original_demands_df.to_excel(writer1,sheet_name='original') 

### Calculating Energy and Cost ###
pump_energy_original = energy_cost(wn,results,Tariff[T])
total_hourly_demand_original = total_hourly_demand(wn,water_tariff[T])

original_energy = pump_energy_original['Energy (kWh)'].sum()
original_cost = pump_energy_original['Cost'].sum()
original_revenue = total_hourly_demand_original["Revenue ($)"].sum()
original_net = original_revenue - original_cost

hourly_results['Original Demand'] = total_hourly_demand_original['Total Demands'].round(3)
hourly_results['Original Energy Consumption (KWh)'] = pump_energy_original['Energy (kWh)']
hourly_results['Original Energy Cost'] = pump_energy_original['Cost']
hourly_results['Original Revenue'] = total_hourly_demand_original["Revenue ($)"]
hourly_results['Original Net'] = hourly_results['Original Revenue'] - hourly_results['Original Energy Cost']

#####################################################################################################
### Second Part: WNTR Simulation of Network Under Different Elasticities with New Demand Patterns ###

### Defining response_details dataframe to track shifted demand ###
response_details = pd.DataFrame()

### producing new demand patterns ###  
new_demands_df = original_demands_df.copy()
for demand in new_demands_df.columns:
    QT = 0
    response_details.at[demand,'Demand Before'] = original_demands_df[demand].sum()
    for hour in new_demands_df.index:
        if water_tariff.loc[hour,T] > water_tariff[T].mean():
            new_demands_df.at[hour,demand] = abs((e)*(water_tariff.loc[hour,T] - water_tariff[T].mean())
                                                 *(original_demands_df.loc[hour,demand]) - original_demands_df.loc[hour,demand])
            QT += abs(original_demands_df.loc[hour,demand] - new_demands_df.loc[hour,demand])       
    response_details.at[demand,'shifted demand'] = round(QT,3)   
    response_details.at[demand,'% of demand shifted'] = round((QT*100)/original_demands_df[demand].sum(),2)
    
    for hour in new_demands_df.index:
        if water_tariff.loc[hour,T] < water_tariff[T].mean():
            Delta = (QT/RT)*abs(water_tariff[T].mean() - water_tariff.loc[hour,T])
            new_demands_df.at[hour,demand] = original_demands_df.loc[hour,demand] + Delta
    response_details.at[demand,'Demand After'] = new_demands_df[demand].sum()
    
### Assigning new demands to WDS and checking the success of the operation ###
wn.assign_demand(new_demands_df,pattern_prefix = str(random.random()))
altered_demand = all_demands(wn) 

### Simulation ###
sim = wntr.sim.EpanetSimulator(wn)
results_sim = sim.run_sim()

### Calculating Energy and Cost ###
pump_energy = energy_cost(wn,results_sim,Tariff[T])
total_hourly_demand_new = total_hourly_demand(wn,water_tariff[T])

new_energy = pump_energy['Energy (kWh)'].sum()
new_cost = pump_energy['Cost'].sum()
new_revenue = total_hourly_demand_new["Revenue ($)"].sum()
new_net = new_revenue - new_cost

### new demands to excel ###
new_demands_df.to_excel(writer1, sheet_name='Optimum')

### Exporting to Summary Dataframe ###
summary.at['value','energy_savings_percentage'] = round((new_energy - original_energy)*100/original_energy ,2)
summary.at['value','cost_savings_percentage'] = round((original_cost - new_cost)*100/original_cost,2)
summary.at['value','revenue_increase_percentage'] = round((new_revenue - original_revenue)*100/original_revenue,2)
summary.at['value','net_increase_percentage'] = round((new_net - original_net)*100/abs(original_net),2)
summary.at['value','total_demand_difference'] = round(response_details['Demand Before'].sum() - response_details['Demand After'].sum(),1)
summary.at['value','Demand_shifted_percentage'] = round(response_details['shifted demand'].sum() * 100 / response_details['Demand Before'].sum(),2)

### Exporting to Hourly Results Dataframe ###
hourly_results['New Demand'] = total_hourly_demand_new['Total Demands'].round(3)
hourly_results['Shifted Demand'] = hourly_results['New Demand'] - hourly_results['Original Demand']
hourly_results['% Shifted Demand'] = round(hourly_results['Shifted Demand'] * 100 / hourly_results['Original Demand'],2)
hourly_results['New Energy Consumption (KWh)'] = pump_energy['Energy (kWh)']
hourly_results['Energy Difference'] =  round(hourly_results['Original Energy Consumption (KWh)'] - hourly_results['New Energy Consumption (KWh)'],2)
hourly_results['% Energy Difference'] = round(hourly_results['Energy Difference']*100/hourly_results['Original Energy Consumption (KWh)'].sum(),2)
hourly_results['New Energy Cost'] = pump_energy['Cost']
hourly_results['Cost Difference'] = hourly_results['Original Energy Cost'] - hourly_results['New Energy Cost']
hourly_results['% Cost Differnce'] = round(hourly_results['Cost Difference']*100/hourly_results['Original Energy Cost'].sum(),2)
hourly_results['New Revenue'] = total_hourly_demand_new["Revenue ($)"]
hourly_results['New Net'] = hourly_results['New Revenue'] - hourly_results['New Energy Cost']
hourly_results['Net Difference'] = hourly_results['New Net'] - hourly_results['Original Net']
hourly_results['% Net Difference'] = hourly_results['Net Difference']*100/abs(hourly_results['Original Net'])

writer1.save()
response_details.to_excel(r'3 Our Tariff Results/B. Response_Details.xlsx', header = True)
summary.to_excel(r'3 Our Tariff Results/C. Summary.xlsx',header = True)
hourly_results.to_excel(r'3 Our Tariff Results/D. Hourly Results.xlsx',header = True)

################
### PLOTTING ###
################
plt.style.use('seaborn')
hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]

##############################
### OVERALL ANALYSIS PLOTS ###
T1 = 'Flat'
T2 = 'Symmetric'
T3 = 'Opposite'

plotting_columns = ['Flat', 'Symmetric', 'Opposite', 'R 1', 'R 2', 'R 3', 'R 4', 'R 5', 'R 6', 'R 7', 'R 8', 'R 9',
       'R 10', 'R 11', 'R 12', 'R 13', 'R 14','R 15', 'R 16', 'R 17', 'R 18', 'R 19','R 20', 'R 21', 'R 22', 'R 23', 'R 24',
       'R 25', 'R 26', 'R 27', 'R 28', 'R 29','R 30', 'R 31', 'R 32', 'R 33', 'R 34','R 35', 'R 36', 'R 37', 'R 38', 'R 39',
       'R 40', 'R 41', 'R 42', 'R 43', 'R 44','R 45', 'R 46', 'R 47', 'R 48', 'R 49','R 50']
### 2.1 Cost Savings Percentages 3D ###
### 


df = pd.read_excel('3 Our Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
df.columns = plotting_columns
df2 = pd.DataFrame(columns = ['x','y','z'])
j = 0
for i in df.index:
    for c in df.columns:     
        df2.at[j,'x'] = df.columns.get_loc(c)
        df2.at[j,'y'] = i
        df2.at[j,'z'] = df.loc[i,c]
        j+=1

fig = plt.figure(figsize=(120,75))
ax = fig.gca(projection='3d')
X = df2['x'].tolist()
Y = df2['y'].tolist()
Z = df2['z'].tolist()
fig.suptitle('Cost Savings Percentages across Tariff Scenarios and Elasticities',fontsize = 100,fontweight='bold')
ax.set_xticks(X)
ax.tick_params(axis='x', which='major', pad=35)
ax.set_yticks(Y)
ax.tick_params(axis='y', which='major', pad=40)
zticks = np.arange(0, 9, 0.5).tolist()
ax.set_zticks(zticks)
ax.tick_params(axis='z', which='major', pad=50)
ax.set_xticklabels(df.columns, fontsize = 60, rotation = 90)
ax.xaxis.labelpad = 200
ax.set_yticklabels(Y, fontsize = 60, rotation = -20)
ax.yaxis.labelpad = 130
ax.set_zticklabels(zticks, fontsize = 60)
ax.zaxis.labelpad = 120

ax.set_xlabel('Tariff Scenarios',fontsize = 80,fontweight='bold')
ax.set_ylabel('Elasticities',fontsize = 80,fontweight='bold')
ax.set_zlabel('Cost Saving Percentages',fontsize = 80,fontweight='bold')

ax.plot_trisurf(X,Y,Z,cmap=cm.coolwarm)
plt.savefig('3 Our Tariff Results/2.1 Cost Savings Percentage 3D.png')
plt.close()

### 2.2.1 Cost Savings Percentages 2D ###
###
plt.rc('xtick',labelsize=20)
plt.rc('ytick',labelsize=20)

df3 = df.loc[:,[T1,T2,T3]]

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Cost Savings Percentages across Elasticities (Tariff Scenarios: '+T1+' ,'+T2+' and '+T3+')',fontdict={'fontsize': 30})
ax.set_xlabel('Elasticities' ,fontdict={'fontsize': 30})
ax.set_ylabel('Cost Saving Percentages',fontdict={'fontsize': 30})
ax.set_xticks(df.index)

c = ['b','g','c']
j=0
for i in df3.columns:
    ax.plot(df3.index.tolist(), df3[i].tolist(),c[j], label = i+' Energy Tariff')
    j+=1

ax.legend(fontsize = 20)
plt.savefig('3 Our Tariff Results/2.2.1 Cost Saving Percentage 2D.png')
plt.close()

### 2.2.2 Cost Savings Percentages 2D ###
###
df4 = df.drop([T1,T2,T3], axis = 1)

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Cost Savings Percentages across Elasticities (Random Tariff Scenarios)',fontdict={'fontsize': 30})
ax.set_xlabel('Elasticities' ,fontdict={'fontsize': 30})
ax.set_ylabel('Cost Saving Percentages',fontdict={'fontsize': 30})
ax.set_xticks(df.index)

for i in df4.columns:
    ax.plot(df4.index.tolist(), df4[i].tolist(), color='c')

ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist(),color='r', linestyle='dashdot',linewidth = 3,label = '??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()+df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??+??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()-df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??-??')
ax.legend(fontsize = 20)
plt.savefig('3 Our Tariff Results/2.2.2 Cost Saving Percentage 2D.png')
plt.close()

### 3.1 Revenue Decrease Percentages 3D ###
### 
df = pd.read_excel('3 Our Tariff Results/3.Revenue Increase Percentage.xlsx', index_col=0)
df.columns = plotting_columns
df2 = pd.DataFrame(columns = ['x','y','z'])
j = 0
for i in df.index:
    for c in df.columns:     
        df2.at[j,'x'] = df.columns.get_loc(c)
        df2.at[j,'y'] = i
        df2.at[j,'z'] = df.loc[i,c]*(-1)
        j+=1
fig = plt.figure(figsize=(120,75))
ax = fig.gca(projection='3d')
X = df2['x'].tolist()
Y = df2['y'].tolist()
Z = df2['z'].tolist()
fig.suptitle('Revenue Decrease Percentages across Tariff Scenarios and Elasticities',fontsize = 100,fontweight='bold')
ax.set_xticks(X)
ax.tick_params(axis='x', which='major', pad=35)
ax.set_yticks(Y)
ax.tick_params(axis='y', which='major', pad=40)
zticks = np.arange(0, 12, 2).tolist()
ax.set_zticks(zticks)
ax.tick_params(axis='z', which='major', pad=50)
ax.set_xticklabels(df.columns, fontsize = 60, rotation = 90)
ax.xaxis.labelpad = 200
ax.set_yticklabels(Y, fontsize = 60, rotation = -20)
ax.yaxis.labelpad = 130
ax.set_zticklabels(zticks, fontsize = 60)
ax.zaxis.labelpad = 120

ax.set_xlabel('Tariff Scenario',fontsize = 80,fontweight='bold')
ax.set_ylabel('Elasticities',fontsize = 80,fontweight='bold')
ax.set_zlabel('Revenue Decrease Percentages',fontsize = 80,fontweight='bold')

ax.plot_trisurf(X,Y,Z,cmap=cm.coolwarm)
plt.savefig('3 Our Tariff Results/3.1 Revenue Decrease Percentage 3D.png')
plt.close()

### 3.2.1 Cost Savings Percentages 2D ###
###

df3 = df.loc[:,[T1,T2,T3]]

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Revenue Decrease Percentages across Elasticities (Tariff Scenarios: '+T1+' ,'+T2+' and '+T3+')',fontdict={'fontsize': 30})
ax.set_xlabel('Elasticities' ,fontdict={'fontsize': 30})
ax.set_ylabel('Revenue Decrease Percentages',fontdict={'fontsize': 30})
ax.set_xticks(df.index)

c = ['b','g','c']
j=0
for i in df3.columns:
    ax.plot(df3.index.tolist(), df3[i].tolist(),c[j], label = i+' Energy Tariff')
    j+=1

ax.legend(fontsize = 20)
plt.savefig('3 Our Tariff Results/3.2.1 Revenue Decrease Percentage 2D.png')
plt.close()

### 3.2.2 Cost Savings Percentages 2D ###
###
df4 = df.drop([T1,T2,T3], axis = 1)

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Revenue Decrease Percentages across Elasticities (Random Tariff Scenarios)',fontdict={'fontsize': 30})
ax.set_xlabel('Elasticities' ,fontdict={'fontsize': 30})
ax.set_ylabel('Revenue Decrease Percentages',fontdict={'fontsize': 30})
ax.set_xticks(df.index)

for i in df4.columns:
    ax.plot(df4.index.tolist(), df4[i].tolist(), color='c')

ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist(),color='r', linestyle='dashdot',linewidth = 3,label = '??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()+df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??+??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()-df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??-??')
ax.legend(fontsize = 20)
plt.savefig('3 Our Tariff Results/3.2.2 Revenue Decrease Percentage 2D.png')
plt.close()

### 4.1 Net Increase Percentages 3D ###
### 
df = pd.read_excel('3 Our Tariff Results/4.Net Increase Percentage.xlsx', index_col=0)
df.columns = plotting_columns
df2 = pd.DataFrame(columns = ['x','y','z'])
j = 0
for i in df.index:
    for c in df.columns:     
        df2.at[j,'x'] = df.columns.get_loc(c)
        df2.at[j,'y'] = i
        df2.at[j,'z'] = df.loc[i,c]
        j+=1
fig = plt.figure(figsize=(120,75))
ax = fig.gca(projection='3d')
X = df2['x'].tolist()
Y = df2['y'].tolist()
Z = df2['z'].tolist()
fig.suptitle('Net Increase Percentages across Tariff Scenarios and Elasticities',fontsize = 100,fontweight='bold')
ax.set_xticks(X)
ax.tick_params(axis='x', which='major', pad=35)
ax.set_yticks(Y)
ax.tick_params(axis='y', which='major', pad=40)
zticks = np.arange(0, 8, 1).tolist()
ax.set_zticks(zticks)
ax.tick_params(axis='z', which='major', pad=50)
ax.set_xticklabels(df.columns, fontsize = 60, rotation = 90)
ax.xaxis.labelpad = 200
ax.set_yticklabels(Y, fontsize = 60, rotation = -20)
ax.yaxis.labelpad = 130
ax.set_zticklabels(zticks, fontsize = 60)
ax.zaxis.labelpad = 120

ax.set_xlabel('Tariff Scenarios',fontsize = 80,fontweight='bold')
ax.set_ylabel('Elasticities',fontsize = 80,fontweight='bold')
ax.set_zlabel('Net Increase Percentages',fontsize = 80,fontweight='bold')

ax.plot_trisurf(X,Y,Z,cmap=cm.coolwarm)
plt.savefig('3 Our Tariff Results/4.1 Net Increase Percentage 3D.png')
plt.close()

### 4.2.1 Cost Savings Percentages 2D ###
###

df3 = df.loc[:,[T1,T2,T3]]

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Net Increase Percentages across Elasticities (Tariff Scenarios: '+T1+' ,'+T2+' and '+T3+')',fontdict={'fontsize': 30})
ax.set_xlabel('Elasticities' ,fontdict={'fontsize': 30})
ax.set_ylabel('Net Increase Percentages',fontdict={'fontsize': 30})
ax.set_xticks(df.index)

c = ['b','g','c']
j=0
for i in df3.columns:
    ax.plot(df3.index.tolist(), df3[i].tolist(),c[j], label = i+' Energy Tariff')
    j+=1

plt.savefig('3 Our Tariff Results/4.2.1 Net Increase Percentage 2D.png')
plt.close()

### 4.2.2 Cost Savings Percentages 2D ###
###
df4 = df.drop([T1,T2,T3], axis = 1)

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Net Increase Percentages across Elasticities (Random Tariff Scenarios)',fontdict={'fontsize': 30})
ax.set_xlabel('Elasticities' ,fontdict={'fontsize': 30})
ax.set_ylabel('Net Increase Percentages',fontdict={'fontsize': 30})
ax.set_xticks(df.index)

for i in df4.columns:
    ax.plot(df4.index.tolist(), df4[i].tolist(), color='c')

ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist(),color='r', linestyle='dashdot',linewidth = 3,label = '??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()+df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??+??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()-df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??-??')
ax.legend(fontsize = 20)
plt.savefig('3 Our Tariff Results/4.2.2 Net Increase Percentage 2D.png')
plt.close()


### 6.1 Demand Shifted Percentages 3D ###
### 
df = pd.read_excel('3 Our Tariff Results/6.Demand Shifted Percentage.xlsx', index_col=0)
df.columns = plotting_columns
df2 = pd.DataFrame(columns = ['x','y','z'])
j = 0
for i in df.index:
    for c in df.columns:     
        df2.at[j,'x'] = df.columns.get_loc(c)
        df2.at[j,'y'] = i
        df2.at[j,'z'] = df.loc[i,c]
        j+=1
fig = plt.figure(figsize=(120,75))
ax = fig.gca(projection='3d')
X = df2['x'].tolist()
Y = df2['y'].tolist()
Z = df2['z'].tolist()
fig.suptitle('Demand Shifted Percentages across Tariff Scenarios and Elasticities',fontsize = 100,fontweight='bold')
ax.set_xticks(X)
ax.tick_params(axis='x', which='major', pad=35)
ax.set_yticks(Y)
ax.tick_params(axis='y', which='major', pad=40)
zticks = np.arange(0, 14, 2).tolist()
ax.set_zticks(zticks)
ax.tick_params(axis='z', which='major', pad=50)
ax.set_xticklabels(df.columns, fontsize = 60, rotation = 90)
ax.xaxis.labelpad = 200
ax.set_yticklabels(Y, fontsize = 60, rotation = -20)
ax.yaxis.labelpad = 130
ax.set_zticklabels(zticks, fontsize = 60)
ax.zaxis.labelpad = 120

ax.set_xlabel('Tariff Scenaris',fontsize = 80,fontweight='bold')
ax.set_ylabel('Elasticities',fontsize = 80,fontweight='bold')
ax.set_zlabel('Demand Shifted Percentages',fontsize = 80,fontweight='bold')

ax.plot_trisurf(X,Y,Z,cmap=cm.coolwarm)
plt.savefig('3 Our Tariff Results/6.1 Demand Shifted Percentage 3D.png')
plt.close()

### 6.2.1 Cost Savings Percentages 2D ###
###

df3 = df.loc[:,[T1,T2,T3]]

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Demand Shifted Percentages across Elasticities (Tariff Scenarios: '+T1+' ,'+T2+' and '+T3+')',fontdict={'fontsize': 30})
ax.set_xlabel('Elasticities' ,fontdict={'fontsize': 30})
ax.set_ylabel('Demand Shifted Percentages',fontdict={'fontsize': 30})
ax.set_xticks(df.index)

c = ['b','g','c']
j=0
for i in df3.columns:
    ax.plot(df3.index.tolist(), df3[i].tolist(),c[j], label = i+' Energy Tariff')
    j+=1

ax.legend(fontsize = 20)
plt.savefig('3 Our Tariff Results/6.2.1 Demand Shifted Percentage 2D.png')
plt.close()

### 6.2.2 Cost Savings Percentages 2D ###
###
df4 = df.drop([T1,T2,T3], axis = 1)

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Demand Shifted Percentages across Elasticities (Random Tariff Scenarios)',fontdict={'fontsize': 30})
ax.set_xlabel('Elasticities' ,fontdict={'fontsize': 30})
ax.set_ylabel('Demand Shifted Percentages',fontdict={'fontsize': 30})
ax.set_xticks(df.index)

for i in df4.columns:
    ax.plot(df4.index.tolist(), df4[i].tolist(), color='c')

ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist(),color='r', linestyle='dashdot',linewidth = 3,label = '??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()+df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??+??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()-df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??-??')
ax.legend(fontsize = 20)
plt.savefig('3 Our Tariff Results/6.2.2 Demand Shifted Percentage 2D.png')
plt.close()

###############################
### SPECIFIC ANALYSIS PLOTS ###
plt.rc('xtick',labelsize=15)
plt.rc('ytick',labelsize=15)
T = 'Symmetric'
e = 0.7
hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]

### B Response Details Plots ###
### 
df = pd.read_excel('3 Our Tariff Results/B. Response_Details.xlsx', index_col=0)

### B.1 Box_Plot_%_shifted_demand ###
df.boxplot( '% of demand shifted', figsize = (15,10),fontsize = 15)
plt.title('Box plot of percentage of shifted demand across all demands (Tariff Scenario: '+T+', Elasticity: '+str(e)+')', fontdict={'fontsize': 20})
plt.savefig('3 Our Tariff Results/B.1 % of Demand Shifted.png')
plt.close()

### B.2 Box_Plot_shifted_demand ###
df.boxplot( 'shifted demand', figsize = (15,10),fontsize = 15)
plt.title('Box plot of amount of shifted demand across all demands (Tariff Scenario: '+T+', Elasticity: '+str(e)+')', fontdict={'fontsize': 20})
plt.savefig('3 Our Tariff Results/B.2 Total Demand Shifted.png')
plt.close()

### D Hourly Results Plots ###
### 
df = pd.read_excel('3 Our Tariff Results/D. Hourly Results.xlsx', index_col=0)

### D.1 Comparison_Total Demand & Tariff ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('Original Demand, Altered Demand and Energy Tariff (Tariff Scenario: '+T+', Elasticity: '+str(e)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Water Consumption (GPM)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['Original Demand'].tolist(), color='red', label = 'Original Demand (GPM)')
ax1.plot(hours,df['New Demand'].tolist(),color='green', label = 'Altered Demand (GPM)')
ax1.tick_params(axis='y', labelcolor='red')
ax1.legend(fontsize = 15)
ax2 = ax1.twinx()  
ax2.set_ylabel('Energy Tariff (factor/W)', color='blue',fontdict={'fontsize': 15})  
ax2.step(hours, df['Energy Tariff'], where = 'post',color='blue', linestyle='dotted')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('3 Our Tariff Results/D.1 Comparison_Total Demand & Tariff.png')
plt.close()

### D.2 Comparison_Cost & Energy Tariff ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('BAU and New Energy Cost and Energy Tariff (Tariff Scenario: '+T+', Elasticity: '+str(e)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Energy Cost (factor)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['Original Energy Cost'].tolist(), color='red', label = 'BAU Cost (factor)')
ax1.plot(hours,df['New Energy Cost'].tolist(),color='green', label = 'New Cost (factor)')
ax1.tick_params(axis='y', labelcolor='red')
ax1.legend(fontsize = 15)
ax2 = ax1.twinx()  
ax2.set_ylabel('Energy Tariff(factor/W)', color='blue',fontdict={'fontsize': 15})  
ax2.step(hours, df['Energy Tariff'], where = 'post',color='blue', linestyle='dotted')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('3 Our Tariff Results/D.2 Comparison_Cost & Energy Tariff.png')
plt.close()

### D.3 Comparison Revenue & Water Tariff ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('BAU and New Water Revenue and Water Tariff (Tariff Scenario: '+T+', Elasticity: '+str(e)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Revenue(factor)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['Original Revenue'].tolist(), color='red', label = 'BAU Revenue(factor)')
ax1.plot(hours,df['New Revenue'].tolist(),color='green', label = 'New Revenue(factor)')
ax1.tick_params(axis='y', labelcolor='red')
ax1.legend(fontsize = 15)
ax2 = ax1.twinx()  
ax2.set_ylabel('Water Tariff (factor/GPM)', color='blue',fontdict={'fontsize': 15})  
ax2.step(hours, df['Water Tariff'], where = 'post',color='blue', linestyle='dotted')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('3 Our Tariff Results/D.3 Comparison_Revenue & Water Tariff.png')
plt.close()

### D.4 Comparison Net & Water Tariff ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('BAU and New Water Net and Water Tariff (Tariff Scenario: '+T+', Elasticity: '+str(e)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Net (factor)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['Original Net'].tolist(), color='red', label = 'BAU Net (factor)')
ax1.plot(hours,df['New Net'].tolist(),color='green', label = 'New Net (factor)')
ax1.tick_params(axis='y', labelcolor='red')
ax1.legend(fontsize = 15)
ax2 = ax1.twinx()  
ax2.set_ylabel('Water Tariff (factor/GPM)', color='blue',fontdict={'fontsize': 15})  
ax2.step(hours, df['Water Tariff'], where = 'post',color='blue', linestyle='dotted')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('3 Our Tariff Results/D.4 Comparison_Net & Water Tariff.png')
plt.close()

### D.5 Comparison_shifted_demand_and_energy_difference ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('Shifted Demand and Energy Differences (Tariff Scenario: '+T+', Elasticity: '+str(e)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Shifted Demand (GPM)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['Shifted Demand'].tolist(), color='red')
ax1.tick_params(axis='y', labelcolor='red')
ax2 = ax1.twinx()  
ax2.set_ylabel('Energy Difference (W)', color='blue',fontdict={'fontsize': 15})  
ax2.plot(hours, df['Energy Difference'], color='blue')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('3 Our Tariff Results/D.5 Comparison_shifted_demand_and_energy_difference.png')
plt.close()

### D.6 Demand_&_Energy_original ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('Demand and Energy: Original (Tariff Scenario: '+T+', Elasticity: '+str(e)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Demand (GPM)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['Original Demand'].tolist(), color='red')
ax1.tick_params(axis='y', labelcolor='red')
ax2 = ax1.twinx()  
ax2.set_ylabel('Energy (W)', color='blue',fontdict={'fontsize': 15})  
ax2.plot(hours, df['Original Energy Consumption (KWh)'], color='blue')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('3 Our Tariff Results/D.6 Demand_&_Energy_original.png')
plt.close()

### D.7 Demand_&_Energy_new ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('Demand and Energy: New (Tariff Scenario: '+T+', Elasticity: '+str(e)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Demand (GPM)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['New Demand'].tolist(), color='red')
ax1.tick_params(axis='y', labelcolor='red')
ax2 = ax1.twinx()  
ax2.set_ylabel('Energy Consumption(W)', color='blue',fontdict={'fontsize': 15})  
ax2.plot(hours, df['New Energy Consumption (KWh)'], color='blue')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('3 Our Tariff Results/D.7 Demand_&_Energy_new.png')
plt.close()