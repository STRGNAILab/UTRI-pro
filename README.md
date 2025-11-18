# The Structural Roots of Thermal Inequity
Linking Street Network Thermal Resilience to Socioeconomic Vulnerability

~ The data and code will be fully updated within a week.

## Abstract for our work
As climate change intensifies urban extreme heat events, the role of street network topology in perpetuating thermal inequity remains under-quantified, which is a critical factor governing heat accumulation and dissipation. This paper introduces the Urban Thermal Resilience Index (UTRI), a novel metric grounded in network science principles of permeability, hierarchy, and decentralization, designed to assess the intrinsic heat ventilation potential of street networks. Applying this index to Washington, D.C., we analyze its relationship with socioeconomic data by integrating street network information from OpenStreetMap (OSM) and community data from the American Community Survey (ACS). Our findings reveal a significant positive spatial correlation between a network's thermal resilience and the median household income of its community. Specifically, the structurally deficient street networks with poor thermal performance are disproportionately co-located with socioeconomically vulnerable neighborhoods. This research provides a new perspective on the structural roots of urban thermal vulnerability, using quantitative evidence from the Thermal Risk Vulnerability Index (TRVI), which reveals that the distribution of heat risk is a critical environmental justice issue embedded in street network planning.

## Project Structure
```
.
├── ACS_DATA/               # 1. Code for acquiring and processing socioeconomic data from the United States Census Bureau's American Community Survey (ACS)
├── Climate_DATA/           # 2. Code for acquiring and processing climate data (such as surface temperature)
├── OSM_DATA/               # 3. Code for downloading and preprocessing road network data from OpenStreetMap
├── combine_ACS_and_OSM/    # 4. Core analytical code for data merging, metric calculation and spatial modelling
├── data/                   # Store all raw, intermediate and final datasets (.csv, .shp, .graphml)
├── result_img/             # Store all generated visualisations, maps and result images
├── tl_2022_11_tract.zip    # Original Shapefile geographic boundary files for the Washington, D.C. census tracts
└── README.md               # Project Specification Document
```

---

