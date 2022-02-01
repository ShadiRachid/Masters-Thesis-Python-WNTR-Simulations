# Masters Thesis

## Abstract

With the continuous development and advances in water metering technologies, and the rising necessities to include end-users in the sustainable management of water distribution systems, water utilities are increasingly exploring new demand management strategies. Demand response is a promising strategy that has shown great potential in the energy sector, but is not yet properly investigated in water management. This thesis explores the potential of demand response in reducing energy costs incurred from a WDS’s pumps’ energy consumption, under TOU energy tariff conditions. Simulations are conducted under six different scenarios that investigate different utility signals, decision making, demand modeling and other conditions. Within the boundaries of modeled scenarios and their limitations, DR exhibited high potential of WDS energy cost savings due to water demand shifting. Nonetheless, the thesis provides preliminary evidence on the possible benefits of DR as a water demand management strategy and points out multiple future research topics and domains.
 
## Python

The design, simulation, data manipulation and representation is realized with the coding language “**Python**” (Van Rossum & Drake Jr, 1995). Moreover, it was beneficial to rely on python, since it allows the utilization of the “Water Network Tool for Resilience” (WNTR) library.

## WNTR Library

In order to conduct water network simulations, the python package entitled WNTR is utilized. **WNTR** is a flexible API that is based upon EPANET, which is a tool that allows creating, simulating and observing different variables in water networks. Through WNTR, existing EPANET water networks (.inp files) are imported to be manipulated and simulated in Python. It is possible to modify the network, alter controls, manage different simulation options, and conduct different simulation types on the network (Klise et al., 2017).
The coupling of EPANET and Python, allows for the manipulation of input parameters to the water network simulations, and the utilization of results for different purposes. In our case for instance, we are able to alter demands and run the simulations of the water network with different demands in each case, record the resultant relevant variables, and afterwards conduct our calculations and visualizations.
[WNTR](https://wntr.readthedocs.io/en/latest/)

## Other Python Libraries

Multiple other Python libraries are necessary to complete the objectives of the design. The libraries of **Pandas** (McKinney, 2010) and **Numpy** (Oliphant, 2006) are needed to manipulate tabulated data that are inputs and outputs of the WNTR Library which are in the form of DataFrames or series. Visualization of the data is made possible with the **Matplotlib** library (Hunter, 2007), which also transforms DataFrames into 2D and 3D graphs.

## References

Klise, K. A., Bynum, M., Moriarty, D., & Murray, R. (2017). A software framework for assessing the resilience of drinking water systems to disasters with an example earthquake case study, Environmental Modelling and Software. 95, 420–431. https://doi.org/10.1016/j.envsoft.2017.06.022

McKinney, W. (2010). Data Structures for Statistical Computing in Python. In S. Van der Walt & J. Millman (Eds.), Proceedings of the 9th Python in Science Conference (pp. 56–61). https://doi.org/10.25080/Majora-92bf1922-00a

Oliphant, T. E. (2006). A guide to NumPy. Trelgol Publishing USA.

Van Rossum, G., & Drake Jr, F. L. (1995). Python reference manual. Centrum voor Wiskunde en Informatica Amsterdam.
