import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import wntr


def autolabel(rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=17)


def align_yaxis(ax1, ax2):
    """Align zeros of the two axes, zooming them out by same ratio"""
    axes = (ax1, ax2)
    extrema = [ax.get_ylim() for ax in axes]
    tops = [extr[1] / (extr[1] - extr[0]) for extr in extrema]
    # Ensure that plots (intervals) are ordered bottom to top:
    if tops[0] > tops[1]:
        axes, extrema, tops = [list(reversed(l))
                               for l in (axes, extrema, tops)]

    # How much would the plot overflow if we kept current zoom levels?
    tot_span = tops[1] + 1 - tops[0]

    b_new_t = extrema[0][0] + tot_span * (extrema[0][1] - extrema[0][0])
    t_new_b = extrema[1][1] - tot_span * (extrema[1][1] - extrema[1][0])
    axes[0].set_ylim(extrema[0][0], b_new_t)
    axes[1].set_ylim(t_new_b, extrema[1][1])


### importing water network model ###
inp_file = 'Net3.inp'
wn = wntr.network.WaterNetworkModel(inp_file)
plt.style.use('seaborn')


######################
### S,X,E Analyses ###
cost1 = pd.read_excel('3. Discussion Plots/1.1 Analyses.xlsx', index_col=0)
cost2 = pd.read_excel(
    '1. No Limits/2 Same Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
cost3 = pd.read_excel(
    '1. No Limits/3 Our Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)

### Scenario 1.1###

S = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
X = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
dfs = pd.DataFrame(index=S, columns=['mean'])
dfx = pd.DataFrame(index=X, columns=['mean'])


for s in S:
    df1 = cost1.copy()
    df1 = df1[df1.S == s]
    df1['mean'] = df1.mean(axis=1)
    dfs.at[s, 'mean'] = df1['mean'].mean().round(2)


x = np.arange(len(S))
width = 0.25

fig, ax = plt.subplots(figsize=(18, 7))
rects1 = ax.bar(x, dfs['mean'], width, color='lightgreen')

ax.set_xlabel('Setting', fontsize=17)
ax.set_ylabel('Average Cost Saving Percentage', fontsize=17)
ax.set_title('Scenario 1.1 - Feedback : Average Cost Saving Percentage for Each Setting Value Across All Energy Tariff Scenarios & Uptake Rates', fontsize=18)
ax.set_xticks(x)
ax.set_xticklabels(S, fontsize=17)
y = np.arange(0, 7, 1)
ax.set_yticks(y)
ax.set_yticklabels(y, fontsize=17)
autolabel(rects1)
fig.tight_layout()
plt.savefig('3. Discussion Plots/1_S_Cost Savings.png')

for x in X:
    df1 = cost1.copy()
    df1 = df1[df1.X == x]
    df1['mean'] = df1.mean(axis=1)
    dfx.at[x, 'mean'] = df1['mean'].mean().round(2)

x = np.arange(len(X))
width = 0.25

fig, ax = plt.subplots(figsize=(18, 7))
rects1 = ax.bar(x, dfx['mean'], width, color='lightgreen')

ax.set_xlabel('Uptake Rate', fontsize=17)
ax.set_ylabel('Average Cost Saving Percentage', fontsize=17)
ax.set_title('Scenario 1.1 - Feedback : Average Cost Saving Percentage for Each Uptake Rate Value Across All Energy Tariff Scenarios & Settings', fontsize=18)
ax.set_xticks(x)
ax.set_xticklabels(X, fontsize=17)
y = np.arange(0, 9, 1)
ax.set_yticks(y)
ax.set_yticklabels(y, fontsize=17)
autolabel(rects1)
fig.tight_layout()

plt.savefig('3. Discussion Plots/1_X_Cost Savings.png')


### Scenario 2.1 ###

cost2['mean'] = cost2.mean(axis=1).round(2)

labels = cost2.index
x = np.arange(len(labels))
width = 0.25

fig, ax = plt.subplots(figsize=(18, 7))
rects1 = ax.bar(x, cost2['mean'], width, color='lightgreen')

ax.set_xlabel('Elasticity', fontsize=17)
ax.set_ylabel('Average Cost Saving Percentage', fontsize=17)
ax.set_title('Scenario 2.1 - Adopted Tariff : Average Cost Saving Percentage for Each Elasticity Value Across All Energy Tariff Scenarios', fontsize=18)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=17)
y = np.arange(0, 5, 1)
ax.set_yticks(y)
ax.set_yticklabels(y, fontsize=17)
autolabel(rects1)
fig.tight_layout()
plt.savefig('3. Discussion Plots/2_e_Cost Savings.png')

### Scenario 3.1 ###

cost3['mean'] = cost3.mean(axis=1).round(2)

labels = cost3.index
x = np.arange(len(labels))
width = 0.25

fig, ax = plt.subplots(figsize=(18, 7))
rects1 = ax.bar(x, cost3['mean'], width, color='lightgreen')
ax.set_xlabel('Elasticity', fontsize=17)
ax.set_ylabel('Average Cost Saving Percentage', fontsize=17)
ax.set_title('Scenario 3.1 - Developed Tariff : Average Cost Saving Percentage for Each Elasticity Value Across All Energy Tariff Scenarios', fontsize=18)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=17)
y = np.arange(0, 5, 1)
ax.set_yticks(y)
ax.set_yticklabels(y, fontsize=17)
autolabel(rects1)
fig.tight_layout()
plt.savefig('3. Discussion Plots/3_e_Cost Savings.png')


########################################
### Demand Shifted and Cost Analyses ###

cost1 = pd.read_excel(
    '2. Limited Qmax/1 No Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
cost2 = pd.read_excel(
    '2. Limited Qmax/2 Same Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
cost3 = pd.read_excel(
    '2. Limited Qmax/3 Our Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
demand1 = pd.read_excel(
    '2. Limited Qmax/1 No Tariff Results/4.Demand Shifted Percentage.xlsx', index_col=0)
demand2 = pd.read_excel(
    '2. Limited Qmax/2 Same Tariff Results/6.Demand Shifted Percentage.xlsx', index_col=0)
demand3 = pd.read_excel(
    '2. Limited Qmax/3 Our Tariff Results/6.Demand Shifted Percentage.xlsx', index_col=0)

df = pd.DataFrame(index=cost1.columns)
df['maxcost 1'] = cost1.max(axis=0).round(2)
df['maxcost 2'] = cost2.max(axis=0).round(2)
df['maxcost 3'] = cost3.max(axis=0).round(2)
df['maxdemand 1'] = demand1.max(axis=0).round(2)
df['maxdemand 2'] = demand2.max(axis=0).round(2)
df['maxdemand 3'] = demand3.max(axis=0).round(2)

labels = df.index
x = np.arange(len(labels))
width = 0.28

### Scenario 1.2 ###
fig, ax = plt.subplots(figsize=(20, 10))
ax2 = ax.twinx()

ax.bar(x-width/2, df['maxcost 1'], width,
       color='lightgreen', edgecolor='black')
ax2.bar(x+width/2, df['maxdemand 1'], width, color='violet', edgecolor='black')

ax.set_xlabel('Energy Tariff Scenarios', fontsize=20, fontweight='heavy')
ax.set_ylabel('Cost Saving Percentage', fontsize=20,
              fontweight='heavy', color='lightgreen')
ax.set_title('Scenario 1.2 - Feedback with Limited Demand: Maximum Cost Saving and Demand Shifted Percentages across All Energy Tariff Scenarios', fontsize=18)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation='vertical', fontsize=17)
ax2.set_ylabel('Demand Shifted Percentage', fontsize=20,
               fontweight='heavy', color='violet')

align_yaxis(ax, ax2)
fig.tight_layout()
plt.savefig('3. Discussion Plots/1.2_Costs_demands.png')

### Scenario 2.2 ###
fig, ax = plt.subplots(figsize=(20, 10))
ax2 = ax.twinx()

ax.bar(x-width/2, df['maxcost 2'], width,
       color='lightgreen', edgecolor='black')
ax2.bar(x+width/2, df['maxdemand 2'], width, color='violet', edgecolor='black')

ax.set_xlabel('Energy Tariff Scenarios', fontsize=20, fontweight='heavy')
ax.set_ylabel('Cost Saving Percentage', fontsize=20,
              fontweight='heavy', color='lightgreen')
ax.set_title('Scenario 2.2 - Adopted Tariff with Limited Demand: Maximum Cost Saving and Demand Shifted Percentages across All Energy Tariff Scenarios', fontsize=18)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation='vertical', fontsize=17)
ax2.set_ylabel('Demand Shifted Percentage', fontsize=20,
               fontweight='heavy', color='violet')

align_yaxis(ax, ax2)
fig.tight_layout()
plt.savefig('3. Discussion Plots/2.2_Costs_demands.png')

### Scenario 3.2 ###
fig, ax = plt.subplots(figsize=(20, 10))
ax2 = ax.twinx()

ax.bar(x-width/2, df['maxcost 3'], width,
       color='lightgreen', edgecolor='black')
ax2.bar(x+width/2, df['maxdemand 3'], width, color='violet', edgecolor='black')

ax.set_xlabel('Energy Tariff Scenarios', fontsize=20, fontweight='heavy')
ax.set_ylabel('Cost Saving Percentage', fontsize=20,
              fontweight='heavy', color='lightgreen')
ax.set_title('Scenario 3.2 - Developed Tariff with Limited Demand: Maximum Cost Saving and Demand Shifted Percentages across All Energy Tariff Scenarios', fontsize=18)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation='vertical', fontsize=17)
ax2.set_ylabel('Demand Shifted Percentage', fontsize=20,
               fontweight='heavy', color='violet')

align_yaxis(ax, ax2)
fig.tight_layout()
plt.savefig('3. Discussion Plots/3.2_Costs_demands.png')


################################
### Pie Charts, Cost Savings ###

cost1 = pd.read_excel(
    '1. No Limits/1 No Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
cost2 = pd.read_excel(
    '1. No Limits/2 Same Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
cost3 = pd.read_excel(
    '1. No Limits/3 Our Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)

# Scenario 1.1

positive_values1 = 0
zero_values1 = 0
negative_values1 = 0

for c in cost1.columns:
    for i in cost1.index:
        if cost1.at[i, c] > 0:
            positive_values1 += 1
        elif cost1.at[i, c] == 0:
            zero_values1 += 1
        else:
            negative_values1 += 1

labels = 'Cost Saving ('+str(positive_values1)+')', 'No Cost Difference (' + \
    str(zero_values1)+')', 'Cost Increase ('+str(negative_values1)+')'
sizes = [positive_values1, zero_values1, negative_values1]
colors = ['lightgreen', 'violet', 'tomato']
fig1, ax1 = plt.subplots(figsize=(60, 30))
ax1.set_title('Scenario 1.1 - Feedback: Cost Saving Analysis',
              fontdict={'fontsize': 80})
ax1.pie(sizes, labels=labels, colors=colors, textprops={
        'size': 70, 'weight': 'heavy'}, autopct='%1.1f%%', shadow=True, startangle=0, labeldistance=1)
ax1.axis('equal')
plt.savefig('3. Discussion Plots/1_Cost Savings.png')

# Scenario 2.1

positive_values2 = 0
zero_values2 = 0
negative_values2 = 0

for c in cost2.columns:
    for i in cost2.index:
        if cost2.at[i, c] > 0:
            positive_values2 += 1
        elif cost2.at[i, c] == 0:
            zero_values2 += 1
        else:
            negative_values2 += 1

labels = 'Cost Saving ('+str(positive_values2)+')', 'No Cost Difference (' + \
    str(zero_values2)+')', 'Cost Increase ('+str(negative_values2)+')'
sizes = [positive_values2, zero_values2, negative_values2]
colors = ['lightgreen', 'violet', 'tomato']
fig1, ax1 = plt.subplots(figsize=(60, 30))
ax1.set_title('Scenario 2.1 - Adopted Tariff: Cost Saving Analysis',
              fontdict={'fontsize': 80})
ax1.pie(sizes, labels=labels, colors=colors, textprops={
        'size': 70, 'weight': 'heavy'}, autopct='%1.1f%%', shadow=True, startangle=0, labeldistance=1)
ax1.axis('equal')
plt.savefig('3. Discussion Plots/2_Cost Savings.png')

# Scenario 3.1

positive_values3 = 0
zero_values3 = 0
negative_values3 = 0

for c in cost3.columns:
    for i in cost3.index:
        if cost3.at[i, c] > 0:
            positive_values3 += 1
        elif cost3.at[i, c] == 0:
            zero_values3 += 1
        else:
            negative_values3 += 1

labels = 'Cost Saving ('+str(positive_values3)+')', 'No Cost Difference (' + \
    str(zero_values3)+')', 'Cost Increase ('+str(negative_values3)+')'
sizes = [positive_values3, zero_values3, negative_values3]
colors = ['lightgreen', 'violet', 'tomato']
fig1, ax1 = plt.subplots(figsize=(60, 30))
ax1.set_title('Scenario 3.1 - Developed Tariff: Cost Saving Analysis',
              fontdict={'fontsize': 80})
ax1.pie(sizes, labels=labels, colors=colors, textprops={
        'size': 70, 'weight': 'heavy'}, autopct='%1.1f%%', shadow=True, startangle=0, labeldistance=1)
ax1.axis('equal')
plt.savefig('3. Discussion Plots/3_Cost Savings.png')

# Total

positive_values = positive_values1 + positive_values2 + positive_values3
zero_values = zero_values1 + zero_values2 + zero_values3
negative_values = negative_values1 + negative_values2 + negative_values3


labels = 'Cost Saving ('+str(positive_values)+')', 'No Cost Difference (' + \
    str(zero_values)+')', 'Cost Increase ('+str(negative_values)+')'
sizes = [positive_values, zero_values, negative_values]
colors = ['lightgreen', 'violet', 'tomato']
fig1, ax1 = plt.subplots(figsize=(60, 30))
ax1.set_title('All Scenarios: Cost Saving Analysis', fontdict={'fontsize': 80})
ax1.pie(sizes, labels=labels, colors=colors, textprops={
        'size': 70, 'weight': 'heavy'}, autopct='%1.1f%%', shadow=True, startangle=0, labeldistance=1)
ax1.axis('equal')
plt.savefig('3. Discussion Plots/Cost Savings.png')

######################

### Pump Figures ###
pump = wn.get_link('10')
fig, ax = plt.subplots(figsize=(50, 40))
ax = wntr.graphics.plot_pump_curve(pump, title='Pump 10 (Lake Source) Curve')
plt.savefig('3. Discussion Plots/pump 10 curve.png')

pump = wn.get_link('335')
fig, ax = plt.subplots(figsize=(50, 40))
ax = wntr.graphics.plot_pump_curve(pump, title='Pump 335 (River Source) Curve')
plt.savefig('3. Discussion Plots/pump 335 curve.png')

### Demand Patterns ###
patterns = ['1', '2', '3', '4', '5']
pat = wn.get_pattern('3').multipliers

df = pd.DataFrame()
for p in patterns:
    string = 'Pattern '+str(p)
    df[string] = wn.get_pattern(p).multipliers

df.to_excel('3. Discussion Plots/patterns.xlsx', header=True)

df.plot(subplots=True, figsize=(15, 10),
        sharex=True, xticks=df.index, grid=True)
plt.savefig('3. Discussion Plots/patterns.png')

### Demands ###
cols = ['Multiplier', 'Assigned Pattern']
df = pd.DataFrame(index=wn.junction_name_list, columns=cols)
for name in wn.junction_name_list:
    demand = wn.get_node(name).demand_timeseries_list[0]
    base = demand.base_value
    pat = demand.pattern
    if base != 0:
        df.at[name, 'Assigned Pattern'] = pat
        df.at[name, 'Multiplier'] = base
    else:
        df = df.drop(name)

df.to_excel('3. Discussion Plots/demands.xlsx', header=True)

cols = ['Multiplier', 'Assigned Pattern']
df = pd.DataFrame(columns=cols)
df.to_excel('3. Discussion Plots/demands.xlsx', header=True)
for j in wn.junction_name_list:
    df = pd.read_excel('3. Discussion Plots/demands.xlsx', index_col=0)
    junction = wn.get_node(j)
    # if (junction.demand_timeseries_list[0].base_value !=0):
    df.at[j, 'Assigned Pattern'] = junction.demand_timeseries_list[0].pattern
    df.at[j, 'Multiplier'] = junction.demand_timeseries_list[0].base_value

##########################
### Symmetric Analysis ###

## No Limit SX ##
no_limit_SX_cost = pd.read_excel(
    '1. No Limits/1 No Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
no_limit_SX_demand = pd.read_excel(
    '1. No Limits/1 No Tariff Results/4.Demand Shifted Percentage.xlsx', index_col=0)

## Limited SX ##
limit_SX_cost = pd.read_excel(
    '2. Limited Qmax/1 No Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
limit_SX_demand = pd.read_excel(
    '2. Limited Qmax/1 No Tariff Results/4.Demand Shifted Percentage.xlsx', index_col=0)

## No Limit Same Tariff ##
no_limit_ST_cost = pd.read_excel(
    '1. No Limits/2 Same Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
no_limit_ST_revenue = pd.read_excel(
    '1. No Limits/2 Same Tariff Results/3.Revenue Increase Percentage.xlsx', index_col=0)
no_limit_ST_net = pd.read_excel(
    '1. No Limits/2 Same Tariff Results/4.Net Increase Percentage.xlsx', index_col=0)
no_limit_ST_demand = pd.read_excel(
    '1. No Limits/2 Same Tariff Results/6.Demand Shifted Percentage.xlsx', index_col=0)

## limited Same Tariff ##
limit_ST_cost = pd.read_excel(
    '2. Limited Qmax/2 Same Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
limit_ST_revenue = pd.read_excel(
    '2. Limited Qmax/2 Same Tariff Results/3.Revenue Increase Percentage.xlsx', index_col=0)
limit_ST_net = pd.read_excel(
    '2. Limited Qmax/2 Same Tariff Results/4.Net Increase Percentage.xlsx', index_col=0)
limit_ST_demand = pd.read_excel(
    '2. Limited Qmax/2 Same Tariff Results/6.Demand Shifted Percentage.xlsx', index_col=0)

## No Limit Our Tariff ##
no_limit_OT_cost = pd.read_excel(
    '1. No Limits/3 Our Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
no_limit_OT_revenue = pd.read_excel(
    '1. No Limits/3 Our Tariff Results/3.Revenue Increase Percentage.xlsx', index_col=0)
no_limit_OT_net = pd.read_excel(
    '1. No Limits/3 Our Tariff Results/4.Net Increase Percentage.xlsx', index_col=0)
no_limit_OT_demand = pd.read_excel(
    '1. No Limits/3 Our Tariff Results/6.Demand Shifted Percentage.xlsx', index_col=0)

## limited Our Tariff ##
limit_OT_cost = pd.read_excel(
    '2. Limited Qmax/3 Our Tariff Results/2.Cost Savings Percentage.xlsx', index_col=0)
limit_OT_revenue = pd.read_excel(
    '2. Limited Qmax/3 Our Tariff Results/3.Revenue Increase Percentage.xlsx', index_col=0)
limit_OT_net = pd.read_excel(
    '2. Limited Qmax/3 Our Tariff Results/4.Net Increase Percentage.xlsx', index_col=0)
limit_OT_demand = pd.read_excel(
    '2. Limited Qmax/3 Our Tariff Results/6.Demand Shifted Percentage.xlsx', index_col=0)


plt.style.use('seaborn')

#####################
###1 Tariff PLOTS ###
T = 'Symmetric'

##1.1 No Limit SX ##
df = no_limit_SX_cost[T]
df1 = pd.DataFrame(index=df.index, columns=['x', 'y'])
for i in df.index:
    df1.at[i, 'x'] = df.index.get_loc(i)
    df1.at[i, 'y'] = df.loc[i]
S = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Cost Savings Percentages across Settings & Uptake Rates (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Settings & Uptake Rates Scenarios', fontdict={'fontsize': 15})
ax1.set_ylabel('Cost Saving Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(S)
ax1.plot(df1['x'].tolist(), df1['y'].tolist(), color='red')
plt.savefig('3. Discussion Plots/1.1.1.png')
plt.close()


df = no_limit_SX_demand[T]
df1 = pd.DataFrame(index=df.index, columns=['x', 'y'])
for i in df.index:
    df1.at[i, 'x'] = df.index.get_loc(i)
    df1.at[i, 'y'] = df.loc[i]
S = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Demand Shifted Percentages across Settings & Uptake Rates (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Settings & Uptake Rates Scenarios', fontdict={'fontsize': 15})
ax1.set_ylabel('Demand Shifted Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(S)
ax1.plot(df1['x'].tolist(), df1['y'].tolist(), color='red')
plt.savefig('3. Discussion Plots/1.1.2.png')
plt.close()

##1.2 Limited SX ##
df = limit_SX_cost[T]
df1 = pd.DataFrame(index=df.index, columns=['x', 'y'])
for i in df.index:
    df1.at[i, 'x'] = df.index.get_loc(i)
    df1.at[i, 'y'] = df.loc[i]
S = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Cost Savings Percentages across Settings & Uptake Rates (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Settings & Uptake Rates Scenarios', fontdict={'fontsize': 15})
ax1.set_ylabel('Cost Saving Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(S)
ax1.plot(df1['x'].tolist(), df1['y'].tolist(), color='red')
plt.savefig('3. Discussion Plots/1.2.1.png')
plt.close()


df = limit_SX_demand[T]
df1 = pd.DataFrame(index=df.index, columns=['x', 'y'])
for i in df.index:
    df1.at[i, 'x'] = df.index.get_loc(i)
    df1.at[i, 'y'] = df.loc[i]
S = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Demand Shifted Percentages across Settings & Uptake Rates (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Settings & Uptake Rates Scenarios', fontdict={'fontsize': 15})
ax1.set_ylabel('Demand Shifted Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(S)
ax1.plot(df1['x'].tolist(), df1['y'].tolist(), color='red')
plt.savefig('3. Discussion Plots/1.2.2.png')
plt.close()

##1.3 No Limit ST ##
df = no_limit_ST_cost
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Cost Savings Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Cost Saving Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(X)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.3.1.png')
plt.close()

df = no_limit_ST_revenue
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Revenue Decrease Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Revenue Decrease Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.3.2.png')
plt.close()

df = no_limit_ST_net
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Net Increase Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Net Increase Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.3.3.png')
plt.close()

df = no_limit_ST_demand
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Demand Shifted Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Demand Shifted Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.3.4.png')
plt.close()

##1.4 Limit ST ##
df = limit_ST_cost
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Cost Savings Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Cost Saving Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(X)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.4.1.png')
plt.close()

df = limit_ST_revenue
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Revenue Decrease Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Revenue Decrease Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.4.2.png')
plt.close()

df = limit_ST_net
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Net Increase Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Net Increase Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.4.3.png')
plt.close()

df = limit_ST_demand
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Demand Shifted Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Demand Shifted Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.4.4.png')
plt.close()

##1.5 No Limit OT ##
df = no_limit_OT_cost
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Cost Savings Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Cost Saving Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(X)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.5.1.png')
plt.close()

df = no_limit_OT_revenue
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Revenue Decrease Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Revenue Decrease Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.5.2.png')
plt.close()

df = no_limit_OT_net
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Net Increase Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Net Increase Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.5.3.png')
plt.close()

df = no_limit_OT_demand
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Demand Shifted Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Demand Shifted Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.5.4.png')
plt.close()

##1.6 Limit ST ##
df = limit_OT_cost
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Cost Savings Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Cost Saving Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(X)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.6.1.png')
plt.close()

df = limit_OT_revenue
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Revenue Decrease Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Revenue Decrease Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.6.2.png')
plt.close()

df = limit_OT_net
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Net Increase Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Net Increase Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.6.3.png')
plt.close()

df = limit_OT_demand
X = df.index.tolist()
Y = df[T].tolist()
fig, ax1 = plt.subplots(figsize=(15, 10))
ax1.set_title('Demand Shifted Percentages across Elasticities (Tariff Scenario: ' +
              T+')', fontdict={'fontsize': 20})
ax1.set_xlabel('Elasticity', fontdict={'fontsize': 15})
ax1.set_ylabel('Demand Shifted Percentages', fontdict={'fontsize': 15})
ax1.set_xticks(df.index)
ax1.plot(X, Y, color='red')
plt.savefig('3. Discussion Plots/1.6.4.png')
plt.close()
