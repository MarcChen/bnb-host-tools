- Retrieve_Blocked_days scheduled ! (in Run workflow another )

- Add all fetch methods into one single file 
- Add a method to initialize all Datasets (Parent page & Notion API key & Share integration) and save all results in a file .DATABASES_ID and then github secrets 
- Trouver un moyen de mapper tout les pays à un code Pays pour ploter sur une carte

## Réaliser la liste des graphs suivants :

- [ ]  Ventilation des prixs
    - [ ]  Double histogramme gost vs host payout
    - [ ]  Axe abscisse : Nombre de jour de réservation 

- [ ]  Graphique Mensuel prix
    - [ ]  Y : Prix moyen par nuit
    - [ ]  X : Mois (dépense inputé sur le moi de arrival Date)
- [ ]  Graphique Mensuel
    - [ ]  Y : Box plot nombre de jours d’une réservation
    - [ ]  X : Mois
- [ ]  Map plot (color scale) for all the countries 
- [ ]  Occupency (Mensuel)
    - [ ]  Nombre de jours bouqué
    - [ ]  Nombre de jour réservé
    - [ ]  Nombre de jour innocupés

Faire un graph en absice nombre d’étoiles, et sur le box plot prix par nuit !



--- 

## Map plot solutions

```python
import pandas as pd
import plotly.express as px

# Example DataFrame with country names
df = pd.DataFrame({
    "country": ["Philippines", "New Zealand", "United Kingdom", "India", "Morocco"],
    "value": [10, 20, 30, 40, 50]
})

fig = px.choropleth(
    df,
    locations="country",
    locationmode="country names",  # Tells Plotly to interpret the locations as country names
    color="value",
    title="Choropleth by Country Name"
)
fig.show()
```

```python
# Example DataFrame with ISO-3 country codes
df = pd.DataFrame({
    "iso_code": ["PHL", "NZL", "GBR", "IND", "MAR"],
    "value": [10, 20, 30, 40, 50]
})

fig = px.choropleth(
    df,
    locations="iso_code",
    locationmode="ISO-3",  # Tells Plotly to interpret the locations as ISO-3 country codes
    color="value",
    title="Choropleth by ISO Code"
)
fig.show()
```

```python
import pandas as pd
import plotly.express as px
import pycountry

# Function to convert input (either name or code) to ISO-3 code
def to_iso3(country_input):
    try:
        # Try to interpret as a country name first
        return pycountry.countries.lookup(country_input).alpha_3
    except LookupError:
        # If lookup fails, assume it might already be an ISO code and check length
        if len(country_input) in [2, 3]:
            # Optionally, validate it or convert 2-letter codes to 3-letter ones
            try:
                country = pycountry.countries.get(alpha_2=country_input.upper())
                return country.alpha_3 if country else country_input.upper()
            except Exception:
                return country_input.upper()
        # Otherwise, return the input unchanged or handle as needed
        return country_input.upper()

# Example DataFrame with mixed country identifiers
data = {
    "location": [
        "Philippines", "NZL", "United Kingdom", "United Kingdom", "India", 
        "IND", "Morocco", "FR", "FRA", "France", "OK", "Canada", "CAN", "CA", 
        "United Arab Emirates", "US", "USA"
    ],
    "value": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170]
}
df = pd.DataFrame(data)

# Standardize the 'location' column to ISO-3 codes
df['iso_code'] = df['location'].apply(to_iso3)

# Create a choropleth map using Plotly Express with ISO-3 codes
fig = px.choropleth(
    df,
    locations="iso_code",
    locationmode="ISO-3",  # Use ISO-3 codes for mapping
    color="value",
    title="Choropleth Map with Standardized Country Codes"
)
fig.show()

```