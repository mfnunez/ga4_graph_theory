# GA4 Graph Theory Analytics

Interactive data visualization tool for analyzing Google Analytics 4 (GA4) user navigation patterns using graph theory and network analysis.

## Overview

This Streamlit application visualizes user journeys from GA4 data stored in BigQuery, transforming pageview transitions into interactive network graphs. It applies graph theory algorithms to identify key pages, bottlenecks, user segments, and optimal conversion paths.

## Features

- **Interactive Network Visualization**: Dynamic, zoomable graphs using PyVis
- **Real-time BigQuery Integration**: Direct connection to GA4 data with 5-minute cache
- **Graph Theory Metrics**:
  - **Degree Centrality**: Most connected pages
  - **PageRank**: Most influential pages in user flow
  - **Betweenness Centrality**: Critical navigation bottlenecks
  - **Community Detection**: User behavior segments (Louvain algorithm)
  - **Shortest Path Analysis**: Optimal conversion funnels
  - **Orphaned Pages**: Isolated page clusters
- **Manual Refresh**: Clear cache on-demand to fetch latest data
- **Professional UI**: Gradient design with customizable dark mode

## Architecture

```
BigQuery (GA4 Data)
    ↓
Python/Streamlit App
    ↓ (NetworkX + PyVis)
Interactive Graph Visualization
```

### BigQuery Tables
- `avisia_ga4_nodes`: Page-level metrics (pageview counts)
- `avisia_ga4_edges`: Page transitions (from → to, transition counts)

## Setup

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/mfnunez/ga4_graph_theory.git
cd ga4_graph_theory
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Google Cloud credentials**
```bash
# Set your service account key
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your-service-account-key.json"
```

5. **Run locally**
```bash
streamlit run streamlit_app.py
```

### Docker Deployment

```bash
docker build -t ga4-graph-theory .
docker run -p 8080:8080 ga4-graph-theory
```

## Cloud Run Deployment

This app is designed for Google Cloud Run with automatic deployments from the `main` branch.

### Requirements
- BigQuery dataset: `avisia-training.avisia_graph_theory_analytics`
- Service account with BigQuery read permissions
- Cloud Run service configured with continuous deployment

### Recent Fixes
- ✅ Added `google-cloud-bigquery-storage` for faster data fetching (eliminates REST API warning)
- ✅ Reduced cache TTL from 30 minutes to 5 minutes for fresher data
- ✅ Fixed refresh button placement in sidebar

## Usage

### Navigation
- **Accueil**: Landing page with project overview
- **Graph Analyse**: Interactive graph visualization and metrics
- **Contact**: Support information

### Graph Analysis Tools
- Adjust **PageRank Alpha** slider to fine-tune influence calculations
- Enter **source** and **target** pages for shortest path analysis
- Click **Refresh Data** button to manually clear cache

### Data Aggregation
Pages containing `/productsheet/` are automatically aggregated into a single `productsheet_page` node to reduce graph complexity.

## SQL Setup

Use the provided SQL scripts to create BigQuery tables:

- `ga4_data_prep_nodes.sql`: Creates node table with pageview counts
- `ga4_data_prep_edges.sql`: Creates edge table with transition counts

## Technologies

- **Streamlit**: Web application framework
- **NetworkX**: Graph analysis library
- **PyVis**: Interactive network visualization
- **Google Cloud BigQuery**: Data warehouse
- **Matplotlib**: Static graph plotting
- **Python Louvain**: Community detection algorithm

## Project Structure

```
ga4_graph_theory/
├── streamlit_app.py          # Main Streamlit application
├── network_graph.py           # Jupyter notebook analysis
├── network_graph.ipynb        # Network graph experiments
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── logo_avisia.png           # Branding assets
├── ga4_data_prep_nodes.sql   # BigQuery node table setup
└── ga4_data_prep_edges.sql   # BigQuery edge table setup
```

## License

Developed by Avisia for GA4 analytics visualization.

## Contact

For questions or support: mnunez@avisia.fr
