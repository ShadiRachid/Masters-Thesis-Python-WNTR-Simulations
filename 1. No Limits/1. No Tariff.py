import numpy as np
import pandas as pd
import wntr
import wntr.network.controls as controls
import random
import os
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

### returns series with hourly distribution of total demand in network ###
def total_hourly_demand(wn):
    df = all_demands(wn)
    df['Total Demands'] = df.sum(axis = 1)
    ser = np.array(df['Total Demands'])
    return ser

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

### Design Settings, Uptake Rate, Tariff ###
S = [1,2,3,4,5,6,7,8,9,10,11,12] #all available settings
step = 0.1
X = np.arange(step,1.1,step).round(2).tolist() #uptake rate list
Tariff = pd.read_excel('Tariff.xlsx',index_col=0)

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
    
    ### Opening all different results dataframes ##
    energy_savings_percentage = pd.DataFrame()
    cost_savings_percentage = pd.DataFrame()
    total_demand_difference = pd.DataFrame()
    Demand_shifted_percentage = pd.DataFrame()
    
    ##########################################################################
    ### First Part: WNTR Simulation of Network with Existing Demands (BAU) ### 
    
    ### Simulation ###
    wn.assign_demand(original_demands_df,pattern_prefix = str(random.random()))
    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()
    
    ### Calculating Energy and Cost ###
    pump_energy_original = energy_cost(wn,results,Tariff[T])
    original_energy = pump_energy_original['Energy (kWh)'].sum()
    original_cost = pump_energy_original['Cost'].sum()
    
    ##################################################################################################################
    ### Second Part: WNTR Simulation of Network Under 12 settings and uptake rates series with new demand patterns ###
    
    ### Sorting pump_energy_original dataframe to be used for decision making###
    sorted_df = pump_energy_original.sort_values(["tariff ($/KWh)","Cost"],ascending = True) 
    
    ### Defining response_details dataframe to track shifted demand ###
    response_details = pd.DataFrame(columns = original_demands_df.columns, 
                                    index = ['shifted demand','Demand Before','Demand After','% of demand shifted'])
    
    ### looping over all 12 settings ###
    for s in S:
           
        ### Utility Decision Making ;determining peak and off-peak hours using the sorted df ###
        df_off_peak = sorted_df['Cost'].iloc[0:s]
        off_peak_hours = df_off_peak.index.tolist()
        df_peak = sorted_df['Cost'].iloc[len(sorted_df)-s:len(sorted_df)]
        peak_hours = df_peak.index.tolist()
        
        ### looping over all values of uptake rate ### 
        for x in X:
            ### producing new demand patterns ###  
            new_demands_df = original_demands_df.copy()
            for demand in new_demands_df.columns:
                QT = 0
                response_details.at[demand,'Demand Before'] = original_demands_df[demand].sum()
                for hour in new_demands_df.index:
                    if hour in peak_hours:
                       Delta = new_demands_df.loc[hour,demand]*x
                       new_value = new_demands_df.loc[hour,demand]- Delta
                       new_demands_df.at[hour,demand] = new_value
                       QT += Delta
                response_details.at[demand,'shifted demand'] = QT  
                response_details.at[demand,'% of demand shifted'] = round((QT*100)/original_demands_df[demand].sum(),2)
                Delta2 = QT/s 
                for hour in new_demands_df.index:
                    if hour in off_peak_hours: new_demands_df.at[hour,demand] = new_demands_df.loc[hour,demand]+ Delta2
                response_details.at[demand,'Demand After'] = new_demands_df[demand].sum()
                
            ### Assigning new demands to WDS and checking the success of the operation ###
            wn.assign_demand(new_demands_df,pattern_prefix = str(random.random()))
            altered_demand = all_demands(wn)  
            
            ### Simulation ###
            sim = wntr.sim.EpanetSimulator(wn)
            results_sim = sim.run_sim()
            
            ### Calculating Energy and Cost ###
            pump_energy = energy_cost(wn,results_sim,Tariff[T])
            new_energy = pump_energy['Energy (kWh)'].sum()
            new_cost = pump_energy['Cost'].sum()
            
            ### Filling out the Dataframes ###
            scenario = 'S='+str(s)+' X='+str(x)
            energy_savings_percentage.at[scenario,T] = round((new_energy - original_energy)*100/original_energy ,2)
            cost_savings_percentage.at[scenario,T] = round((original_cost - new_cost)*100/original_cost,2)
            total_demand_difference.at[scenario,T] = round(response_details['Demand Before'].sum() - response_details['Demand After'].sum(),1)
            Demand_shifted_percentage.at[scenario,T] = round(response_details['shifted demand'].sum() * 100 / response_details['Demand Before'].sum(),2)
    
    ### export dataframes to excel files ###
    energy_savings_percentage.to_excel(r'1 No Tariff Results/1.Energy Savings Percentage'+T+'.xlsx',header = True)
    cost_savings_percentage.to_excel(r'1 No Tariff Results/2.Cost Savings Percentage'+T+'.xlsx',header = True)
    total_demand_difference.to_excel(r'1 No Tariff Results/3.Total Demand Difference'+T+'.xlsx',header = True)
    Demand_shifted_percentage.to_excel(r'1 No Tariff Results/4.Demand Shifted Percentage'+T+'.xlsx',header = True)  

### Opening all different results dataframes ##
energy_savings_percentage = pd.DataFrame()
cost_savings_percentage = pd.DataFrame()
total_demand_difference = pd.DataFrame()
Demand_shifted_percentage = pd.DataFrame()
   
for T in Tariff.columns:
    df1 = pd.read_excel('1 No Tariff Results/1.Energy Savings Percentage'+T+'.xlsx',index_col=0)
    df2 = pd.read_excel('1 No Tariff Results/2.Cost Savings Percentage'+T+'.xlsx',index_col=0)
    df3 = pd.read_excel('1 No Tariff Results/3.Total Demand Difference'+T+'.xlsx',index_col=0)
    df4 = pd.read_excel('1 No Tariff Results/4.Demand Shifted Percentage'+T+'.xlsx',index_col=0)
    energy_savings_percentage[T] = df1[T]
    cost_savings_percentage[T] = df2[T]
    total_demand_difference[T] = df3[T]
    Demand_shifted_percentage[T] = df4[T]
    os.remove('1 No Tariff Results/1.Energy Savings Percentage'+T+'.xlsx')
    os.remove('1 No Tariff Results/2.Cost Savings Percentage'+T+'.xlsx')
    os.remove('1 No Tariff Results/3.Total Demand Difference'+T+'.xlsx')
    os.remove('1 No Tariff Results/4.Demand Shifted Percentage'+T+'.xlsx')
    
energy_savings_percentage.to_excel(r'1 No Tariff Results/1.Energy Savings Percentage.xlsx',header = True)
cost_savings_percentage.to_excel(r'1 No Tariff Results/2.Cost Savings Percentage.xlsx',header = True)
total_demand_difference.to_excel(r'1 No Tariff Results/3.Total Demand Difference.xlsx',header = True)
Demand_shifted_percentage.to_excel(r'1 No Tariff Results/4.Demand Shifted Percentage.xlsx',header = True)

##########################
### SPECIFIC ANALYSIS ####
##########################

T = 'Symmetric'
S = 8
X = 0.5
Ta = Tariff[T]

### Opening Dataframes ###
writer1 = pd.ExcelWriter(r'1 No Tariff Results/A. Demands.xlsx', engine='xlsxwriter')
hourly_results = pd.DataFrame(index = [0, 3600, 7200, 10800, 14400, 18000, 21600, 25200, 28800, 32400, 36000, 39600, 
                                       43200, 46800, 50400, 54000, 57600, 61200, 64800, 68400, 72000, 75600, 79200, 82800])
summary = pd.DataFrame( index = ['value'])
hourly_results['Tariff'] = Ta

###########################################################################
### First Part: WNTR Simulation and Results with Existing Demands (BAU) ### 

### Simulation ###
wn.assign_demand(original_demands_df,pattern_prefix = str(random.random()))
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()

### returning dataframe of original demands and adding it to excel file ###
original_demands_df = all_demands(wn)
original_demands_df.to_excel(writer1,sheet_name='original')

### Original Total Hourly Demand ###
hourly_results['Original Demand'] = total_hourly_demand(wn).round(3)

### Values of Energy and Cost with original Demand###
pump_energy_original = energy_cost(wn,results,Ta)
hourly_results['Original Energy Consumption (KWh)'] = pump_energy_original['Energy (kWh)']
hourly_results['Original Cost'] = pump_energy_original['Cost']

#################################################################################
### Second Part:Utility Decision Making: classifying peak and  off-peak hours ###

sorted_df = pump_energy_original.sort_values(["tariff ($/KWh)","Cost"],ascending = True) 
df_off_peak = sorted_df["Cost"].iloc[0:S]
off_peak_hours = df_off_peak.index.tolist() 
df_peak = sorted_df["Cost"].iloc[len(sorted_df)-S:len(sorted_df)]
peak_hours = df_peak.index.tolist()

################################################################################
### Third Part: Producing New Demand Patterns and Simulating Again with WNTR ###

### Defining response_details dataframe to track shifted demand ###
response_details = pd.DataFrame(index = original_demands_df.columns, 
                                columns = ['shifted demand','Demand Before','Demand After','% of demand shifted'])

### producing new demand patterns ###  
new_demands_df = original_demands_df.copy()
for demand in new_demands_df.columns:
    QT = 0
    response_details.at[demand,'Demand Before'] = original_demands_df[demand].sum()
    for hour in new_demands_df.index:
        if hour in peak_hours:
           Delta = new_demands_df.loc[hour,demand]*X
           new_value = new_demands_df.loc[hour,demand]- Delta
           new_demands_df.at[hour,demand] = new_value
           QT += Delta
    response_details.at[demand, 'shifted demand'] = QT
    response_details.at[demand, '% of demand shifted'] = round((QT*100)/original_demands_df[demand].sum(),2)
    Delta2 = QT/S 
    for hour in new_demands_df.index:
        if hour in off_peak_hours: new_demands_df.at[hour,demand] = new_demands_df.loc[hour,demand]+ Delta2
    response_details.at[demand, 'Demand After'] = new_demands_df[demand].sum()
        
### Assigning new demands to WDS###
wn.assign_demand(new_demands_df,pattern_prefix = 'new')
altered_demand = all_demands(wn)
    
### Simulation with New Demands ###
sim = wntr.sim.EpanetSimulator(wn)
results_sim = sim.run_sim()
    
### Calculating Energy and Cost ###
pump_energy = energy_cost(wn,results_sim,Ta)

### new demands to excel ###
new_demands_df.to_excel(writer1, sheet_name='Optimum')

### Exporting to Hourly Results Dataframe ###
hourly_results['New Demand'] = total_hourly_demand(wn).round(3)
hourly_results['Shifted Demand'] = hourly_results['New Demand'] - hourly_results['Original Demand']
hourly_results['% Shifted Demand'] = round(hourly_results['Shifted Demand'] * 100 / hourly_results['Original Demand'],2)
hourly_results['New Energy Consumption (KWh)'] = pump_energy['Energy (kWh)']
hourly_results['Energy Difference'] =  round(hourly_results['Original Energy Consumption (KWh)'] - hourly_results['New Energy Consumption (KWh)'],2)
hourly_results['% Energy Difference'] = round(hourly_results['Energy Difference']*100/hourly_results['Original Energy Consumption (KWh)'].sum(),2)
hourly_results['New Cost'] = pump_energy['Cost']
hourly_results['Cost Difference'] = hourly_results['Original Cost'] - hourly_results['New Cost']
hourly_results[' % Cost Differnce'] = round(hourly_results['Cost Difference']*100/hourly_results['Original Cost'].sum(),2)

### Exporting to Summary Dataframe ###
summary.at['value','Total Shifted Demand'] = response_details['shifted demand'].sum()
summary.at['value','Percentage Shifted Demand'] = round((summary.loc['value','Total Shifted Demand']*100)/response_details['Demand Before'].sum(),2) 
summary.at['value','Energy Consumption'] = pump_energy['Energy (kWh)'].sum()
summary.at['value','Energy Savings'] = round(pump_energy_original["Energy (kWh)"].sum()-summary.loc['value','Energy Consumption'],2)
summary.at['value','% of Energy Savings'] = round(summary.loc['value','Energy Savings']*100/ pump_energy_original["Energy (kWh)"].sum(),2)
summary.at['value','Energy Cost'] = round(pump_energy["Cost"].sum(),2)
summary.at['value','Cost Savings'] = round(pump_energy_original["Cost"].sum()-summary.loc['value','Energy Cost'],2)
summary.at['value','% of Cost Savings'] = round(summary.loc['value','Cost Savings']*100/pump_energy_original["Cost"].sum(),2)

### exporting results to excel ###
writer1.save()
response_details.to_excel(r'1 No Tariff Results/B. Response_Details.xlsx', header = True)
sorted_df.to_excel(r'1 No Tariff Results/C. Sorted_hours.xlsx',header = True)
summary.to_excel(r'1 No Tariff Results/D. Summary.xlsx',header = True)
hourly_results.to_excel(r'1 No Tariff Results/E. Hourly Results.xlsx',header = True)


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
S = [0,10,20,30,40,50,60,70,80,90,100,110]
yticks = ['S = 1, X = 0.1','S = 2, X = 0.1','S = 3, X = 0.1','S = 4, X = 0.1','S = 5, X = 0.1','S = 6, X = 0.1',
          'S = 7, X = 0.1','S = 7, X = 0.1','S = 9, X = 0.1','S = 10, X = 0.1','S = 11, X = 0.1','S = 12, X = 0.1']

plotting_columns = ['Flat', 'Symmetric', 'Opposite', 'R 1', 'R 2', 'R 3', 'R 4', 'R 5', 'R 6', 'R 7', 'R 8', 'R 9',
       'R 10', 'R 11', 'R 12', 'R 13', 'R 14','R 15', 'R 16', 'R 17', 'R 18', 'R 19','R 20', 'R 21', 'R 22', 'R 23', 'R 24',
       'R 25', 'R 26', 'R 27', 'R 28', 'R 29','R 30', 'R 31', 'R 32', 'R 33', 'R 34','R 35', 'R 36', 'R 37', 'R 38', 'R 39',
       'R 40', 'R 41', 'R 42', 'R 43', 'R 44','R 45', 'R 46', 'R 47', 'R 48', 'R 49','R 50']

### 2.1 Cost Savings Percentages 3D ###
### 
df = pd.read_excel('1 No Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)

df2 = pd.DataFrame(columns = ['x','y','z'])
j = 0
for i in df.index:
    for c in df.columns:     
        df2.at[j,'x'] = df.columns.get_loc(c)
        df2.at[j,'y'] = df.index.get_loc(i)
        df2.at[j,'z'] = df.loc[i,c]
        j+=1

fig = plt.figure(figsize=(120,75))
ax = fig.gca(projection='3d')
X = df2['x'].tolist()
Y = df2['y'].tolist()
Z = df2['z'].tolist()
fig.suptitle('Cost Savings Percentages across All Scenarios, Settings, and Uptake Rates',fontsize = 100,fontweight='bold')
ax.set_xticks(X)
ax.tick_params(axis='x', which='major', pad=35)
ax.set_xticklabels(plotting_columns, fontsize = 60, rotation = 'vertical')
ax.set_xlabel('Energy Scenarios',fontsize = 80,fontweight='bold')
ax.xaxis.labelpad = 200
ax.set_yticks(S)
ax.tick_params(axis='y', which='major', pad=20)
ax.set_ylabel('Settings and Uptake Rates Scenarios',fontsize = 80,fontweight='bold')
ax.set_yticklabels(yticks, fontsize = 60)
ax.yaxis.labelpad = 200
zticks = np.arange(0, 30, 5).tolist()
ax.set_zticks(zticks)
ax.tick_params(axis='z', which='major', pad=50)
ax.set_zticklabels(zticks, fontsize = 60)
ax.set_zlabel('Cost Saving Percentages (%)',fontsize = 80,fontweight='bold')
ax.zaxis.labelpad = 120
ax.plot_trisurf(X,Y,Z,cmap=cm.coolwarm)
plt.savefig('1 No Tariff Results/2.1 Cost Savings Percentage 3D.png')
plt.close()

### 2.2.1 Cost Savings Percentages 2D ###
###
plt.rc('xtick',labelsize=20)
plt.rc('ytick',labelsize=20)

df3 = df.loc[:,[T1,T2,T3]]

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Cost Savings Percentages across Settings & Uptake Rates (Tariff Scenarios: '+T1+' ,'+T2+' and '+T3+')',fontdict={'fontsize': 30})
ax.set_xlabel('Settings & Uptake Rates Scenarios' ,fontdict={'fontsize': 30})
ax.set_ylabel('Cost Saving Percentages',fontdict={'fontsize': 30})
ax.set_xticks(S)
c = ['b','g','c']
j=0
for i in df3.columns:
    ax.plot(df3.index.tolist(), df3[i].tolist(),c[j], label = i+' Energy Tariff')
    j+=1

ax.legend(fontsize = 20)
plt.savefig('1 No Tariff Results/2.2.1 Cost Saving Percentage 2D.png')
plt.close()

### 2.2.2 Cost Savings Percentages 2D ###
###
df4 = df.drop([T1,T2,T3], axis = 1)

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Cost Savings Percentages across Settings & Uptake Rates (Random Tariff Scenarios)',fontdict={'fontsize': 30})
ax.set_xlabel('Settings & Uptake Rates Scenarios' ,fontdict={'fontsize': 30})
ax.set_ylabel('Cost Saving Percentages',fontdict={'fontsize': 30})
ax.set_xticks(S)

for i in df4.columns:
    ax.plot(df4.index.tolist(), df4[i].tolist(), color='c')

ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist(),color='r', linestyle='dashdot',linewidth = 3,label = '??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()+df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??+??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()-df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??-??')
ax.legend(fontsize = 20)
plt.savefig('1 No Tariff Results/2.2.2 Cost Saving Percentage 2D.png')
plt.close()
''
### 4.1 Demand Shifted Percentages 3D ###
### 
df = pd.read_excel('1 No Tariff Results/4.Demand Shifted Percentage.xlsx', index_col=0)

df2 = pd.DataFrame(columns = ['x','y','z'])
j = 0
for i in df.index:
    for c in df.columns:     
        df2.at[j,'x'] = df.columns.get_loc(c)
        df2.at[j,'y'] = df.index.get_loc(i)
        df2.at[j,'z'] = df.loc[i,c]
        j+=1

fig = plt.figure(figsize=(120,75))
ax = fig.gca(projection='3d')
X = df2['x'].tolist()
Y = df2['y'].tolist()
Z = df2['z'].tolist()
fig.suptitle('Demand Shifted Percentages across All Scenarios, Settings, and Uptake Rates', fontsize = 100,fontweight='bold')
ax.set_xticks(X)
ax.tick_params(axis='x', which='major', pad=35)
ax.set_xticklabels(plotting_columns, fontsize = 60, rotation = 'vertical')
ax.set_xlabel('Energy Scenarios',fontsize = 80,fontweight='bold')
ax.xaxis.labelpad = 200
ax.set_yticks(S)
ax.tick_params(axis='y', which='major', pad=20)
ax.set_ylabel('Settings and Uptake Rates Scenarios',fontsize = 80,fontweight='bold')
ax.set_yticklabels(yticks, fontsize = 60)
ax.yaxis.labelpad = 200
ax.set_zlabel('Demand Shifted Percentages',fontsize = 80,fontweight='bold')
ax.zaxis.labelpad = 120
zticks = np.arange(0, 60, 10).tolist()
ax.set_zticks(zticks)
ax.set_zticklabels(zticks, fontsize = 60)
ax.tick_params(axis='z', which='major', pad=50)
ax.plot_trisurf(X,Y,Z,cmap=cm.coolwarm)
plt.savefig('1 No Tariff Results/4.1 Demand Shifted Percentage.png')
plt.close()

### 4.2.1 Demand Shifted Percentages 2D ###
###
plt.rc('xtick',labelsize=20)
plt.rc('ytick',labelsize=20)

df3 = df.loc[:,[T1,T2,T3]]

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Demand Shifted Percentages across Settings & Uptake Rates (Tariff Scenarios: '+T1+' ,'+T2+' and '+T3+')',fontdict={'fontsize': 30})
ax.set_xlabel('Settings & Uptake Rates Scenarios' ,fontdict={'fontsize': 30})
ax.set_ylabel('Demand Shifted Percentages',fontdict={'fontsize': 30})
ax.set_xticks(S)

c = ['b','g','c']
j=0
for i in df3.columns:
    ax.plot(df3.index.tolist(), df3[i].tolist(),c[j], label = i+' Energy Tariff')
    j+=1

ax.legend(fontsize = 20)
plt.savefig('1 No Tariff Results/4.2.1 Demand Shifted Percentage 2D.png')
plt.close()

### 4.2.2 Demand Shifted Percentages 22D ###
###
df4 = df.drop([T1,T2,T3], axis = 1)

fig, ax = plt.subplots(figsize=(25,10))
ax.set_title('Demand Shifted Percentages across Settings & Uptake Rates (Random Tariff Scenarios)',fontdict={'fontsize': 30})
ax.set_xlabel('Settings & Uptake Rates Scenarios' ,fontdict={'fontsize': 30})
ax.set_ylabel('Demand Shifted Percentages',fontdict={'fontsize': 30})
ax.set_xticks(S)

for i in df4.columns:
    ax.plot(df4.index.tolist(), df4[i].tolist(), color='c')

ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist(),color='r', linestyle='dashdot',linewidth = 3,label = '??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()+df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??+??')
ax.plot(df4.index.tolist(), df4.mean(axis = 1).tolist()-df4.std(axis = 1),color='r', linestyle='dotted',linewidth = 3,label = '??-??')
ax.legend(fontsize = 20)
plt.savefig('1 No Tariff Results/4.2.2 Demand Shifted Percentage 2D.png')
plt.close()


###############################
### SPECIFIC ANALYSIS PLOTS ###
plt.rc('xtick',labelsize=15)
plt.rc('ytick',labelsize=15)

T = 'Symmetric'
S = 8
X = 0.5
hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
### B Response Details Plots ###
### 
df = pd.read_excel('1 No Tariff Results/B. Response_Details.xlsx', index_col=0)

### B.1 Box_Plot_%_shifted_demand ###
df.boxplot( '% of demand shifted', figsize = (15,10),fontsize = 15)
plt.title('Box plot of percentage of shifted demand across all demands (Tariff Scenario: '+T+', S: '+str(S)+', X: '+str(X)+')', fontdict={'fontsize': 20})
plt.savefig('1 No Tariff Results/B.1 % of Demand Shifted.png')
plt.close()

### B.2 Box_Plot_shifted_demand ###
df.boxplot( 'shifted demand', figsize = (15,10),fontsize = 15)
plt.title('Box plot of amount of shifted demand across all demands (Tariff Scenario: '+T+', S: '+str(S)+', X: '+str(X)+')', fontdict={'fontsize': 20})
plt.savefig('1 No Tariff Results/B.2 Total Demand Shifted.png')
plt.close()

### E Hourly Results Plots ###
### 
df = pd.read_excel('1 No Tariff Results/E. Hourly Results.xlsx', index_col=0)

### E.1 Comparison_Total Demand & Tariff ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('Original Demand, Altered Demand and Energy Tariff (Tariff Scenario: '+T+', S: '+str(S)+', X: '+str(X)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Water Consumption (GPM)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['Original Demand'].tolist(), color='red', label = 'Original Demand (GPM)')
ax1.plot(hours,df['New Demand'].tolist(),color='green', label = 'Altered Demand (GPM)')
ax1.tick_params(axis='y', labelcolor='red')
ax1.legend(fontsize = 15)
ax2 = ax1.twinx()  
ax2.set_ylabel('Energy Tariff (factor/W)', color='blue',fontdict={'fontsize': 15})  
ax2.step(hours, df['Tariff'], where = 'post',color='blue', linestyle='dotted')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('1 No Tariff Results/E.1 Comparison_Total Demand & Tariff.png')
plt.close()

### E.2 Comparison_Cost & Energy Tariff ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('BAU and New Energy Cost and Energy Tariff (Tariff Scenario: '+T+', S: '+str(S)+', X: '+str(X)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Energy Cost (factor)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['Original Cost'].tolist(), color='red', label = 'BAU Cost (factor)')
ax1.plot(hours,df['New Cost'].tolist(),color='green', label = 'New Cost (factor)')
ax1.tick_params(axis='y', labelcolor='red')
ax1.legend(fontsize = 15)
ax2 = ax1.twinx()  
ax2.set_ylabel('Energy Tariff (factor/W)', color='blue',fontdict={'fontsize': 15})  
ax2.step(hours, df['Tariff'], where = 'post',color='blue', linestyle='dotted')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('1 No Tariff Results/E.2 Comparison_Cost & Energy Tariff.png')
plt.close()

### E.3 Comparison_shifted_demand_and_energy_difference ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('Shifted Demand and Energy Differences (Tariff Scenario: '+T+', S: '+str(S)+', X: '+str(X)+')',fontdict={'fontsize': 20})
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
plt.savefig('1 No Tariff Results/E.3 Comparison_shifted_demand_and_energy_difference.png')
plt.close()

### E.4 Demand_&_Energy_original ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('Demand and Energy: Original (Tariff Scenario: '+T+', S: '+str(S)+', X: '+str(X)+')',fontdict={'fontsize': 20})
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
plt.savefig('1 No Tariff Results/E.4 Demand_&_Energy_original.png')
plt.close()

### E.5 Demand_&_Energy_new ###
fig, ax1 = plt.subplots(figsize=(15,10))
ax1.set_title('Demand and Energy: New (Tariff Scenario: '+T+', S: '+str(S)+', X: '+str(X)+')',fontdict={'fontsize': 20})
ax1.set_xlabel('time (h)',fontdict={'fontsize': 15})
ax1.set_ylabel('Demand (GPM)', color='red',fontdict={'fontsize': 15})
ax1.set_xticks(hours)
ax1.plot(hours, df['New Demand'].tolist(), color='red')
ax1.tick_params(axis='y', labelcolor='red')
ax2 = ax1.twinx()  
ax2.set_ylabel('Energy (W)', color='blue',fontdict={'fontsize': 15})  
ax2.plot(hours, df['New Energy Consumption (KWh)'], color='blue')
ax2.tick_params(axis='y', labelcolor='blue')
fig.tight_layout() 
plt.savefig('1 No Tariff Results/E.5 Demand_&_Energy_new.png')
plt.close()