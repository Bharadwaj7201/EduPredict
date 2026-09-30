# EduPredict MVP - Data Dictionary

Documentation of all data sources and fields.

## bls_salary_data.csv

**Description:** Bureau of Labor Statistics salary data for tech occupations

**Source:** [BLS Occupational Employment and Wage Statistics (May 2023)](https://www.bls.gov/oes/)

### Fields

- `state`: State abbreviation (CT, NY, MA)
- `occupation_code`: BLS SOC code (15-1250 = Computer Occupations, 15-1256 = Data Scientists)
- `occupation_name`: Job title/description
- `median_salary`: Median annual wage (USD)
- `mean_salary`: Mean annual wage (USD)
- `year`: Data year (2023)

---

## ipeds_institutions.csv

**Description:** List of 4-year institutions in CT, NY, MA

**Source:** [IPEDS Institutional Characteristics](https://nces.ed.gov/ipeds/)

### Fields

- `unitid`: IPEDS unique institution identifier
- `institution_name`: Official institution name
- `state`: State abbreviation
- `institution_type`: Public or Private
- `sector`: Institution sector (4-year only for MVP)

---

## ipeds_enrollment_sample.csv

**Description:** Sample AI program enrollment estimates by institution

**Source:** [Estimated based on IPEDS patterns (replace with actual completions data)](https://nces.ed.gov/ipeds/datacenter/Completions.aspx)

### Fields

- `unitid`: IPEDS unique institution identifier
- `institution_name`: Institution name
- `state`: State abbreviation
- `institution_type`: Public or Private
- `program`: Program type (MS in AI, BS in AI, AI in Cybersecurity)
- `student_type`: International or Domestic
- `estimated_enrollment_2023`: Estimated enrollment count
- `year`: Academic year
- `data_source`: Source of data (estimated or actual)
- `cip_code`: Classification of Instructional Programs code
- `note`: Additional notes about the data

---

## job_market_data.csv

**Description:** AI/tech job market indicators by state

**Source:** [BLS Employment Projections + industry analysis](https://www.bls.gov/emp/)

### Fields

- `state`: State abbreviation
- `ai_job_growth_5yr`: Projected AI job growth percentage (2023-2028)
- `tech_job_growth_5yr`: Projected tech job growth percentage
- `demand_level`: Qualitative demand assessment
- `open_positions_sample`: Sample count of open AI-related positions
- `top_employers`: Major employers hiring for AI roles

---

