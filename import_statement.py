import pandas as pd
import requests
import re
from urllib.parse import quote


# ============================================================
# KONFIGURASI
# ============================================================

SPARQL_ENDPOINT = (
     "http://Pujis-MacBook-Pro.local:7200/repositories/Political-Ontology/statements"
)
IRI_SCHEMA = "http://ugm.ac.id/ontology/political-ontology/sch#"
ONTOLOGY = "http://ugm.ac.id/ontology/political-ontology/data#"


# ============================================================
# FILE EXCEL
# ============================================================

NEWS_FILE = "News.xlsx"
PERSON_FILE = "Person.xlsx"
STATEMENT_FILE = "Statement.xlsx"
STANCE_FILE = "Stance.xlsx"
STANCE_TYPE_FILE = "StanceType.xlsx"


# ============================================================
# PREFIX
# ============================================================

PREFIX = f"""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX sch: <{IRI_SCHEMA}> 
PREFIX data: <{ONTOLOGY}>
"""


# ============================================================
# FUNGSI ESCAPE STRING SPARQL
# ============================================================

def sparql_literal(value):
    """
    Mengubah nilai Python menjadi literal SPARQL.
    """

    if pd.isna(value):
        return '""'

    value = str(value)

    value = (
        value
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )

    return f'"{value}"'


# ============================================================
# FUNGSI MEMBUAT IRI
# ============================================================

def iri(local_name):
    """
    Menghasilkan IRI individual ontology.

    Contoh:
    Statement_00001
    ->
    data:Statement_00001
    """

    local_name = str(local_name).strip()

    # Bersihkan karakter yang tidak aman untuk local name
    local_name = re.sub(r"[^A-Za-z0-9_\-]", "_", local_name)

    return f"data:{local_name}"


# ============================================================
# FUNGSI DATE TIME
# ============================================================

def datetime_literal(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return f'"{value}"^^xsd:dateTime'


# ============================================================
# MEMBACA EXCEL
# ============================================================

news_df = pd.read_excel(NEWS_FILE)

person_df = pd.read_excel(PERSON_FILE)

statement_df = pd.read_excel(STATEMENT_FILE)

stance_df = pd.read_excel(STANCE_FILE)

stance_type_df = pd.read_excel(STANCE_TYPE_FILE)


print("Data berhasil dibaca:")
print("News      :", len(news_df))
print("Statement :", len(statement_df))
print("Stance    :", len(stance_df))
print("StanceType:", len(stance_type_df))


# ============================================================
# MEMBUAT TRIPLE
# ============================================================

triples = []

# ============================================================
# 1. Memasukan Object Properties
# ============================================================
triples.append(
    f"sch:madeBy rdf:type owl:ObjectProperty ."
    f"sch:madeBy rdfs:domain sch:Statement ."
    f"sch:madeBy rdfs:range sch:Person ."

    f"sch:expressesStance rdf:type owl:ObjectProperty ."
    f"sch:expressesStance rdfs:domain sch:Statement ."
    f"sch:expressesStance rdfs:range sch:Stance ."

    f"sch:hasStanceType rdf:type owl:ObjectProperty ."
    f"sch:hasStanceType rdfs:domain sch:Stance ."
    f"sch:hasStanceType rdfs:range sch:StanceType ."

    f"sch:hasStatement rdf:type owl:ObjectProperty ."
    f"sch:hasStatement rdfs:domain sch:News ."
    f"sch:hasStatement rdfs:range sch:Statement ."
)

# ============================================================
# 2. Memasukan Data Properties
# ============================================================
triples.append(
    f"sch:textStatement rdf:type owl:DatatypeProperty ."
    f"sch:textStatement rdfs:domain sch:Statement ."
    f"sch:textStatement rdfs:range xsd:string ."

    f"sch:personName rdf:type owl:DatatypeProperty ."
    f"sch:personName rdfs:domain sch:Person ."
    f"sch:personName rdfs:range xsd:string ."

    f"sch:title rdf:type owl:DatatypeProperty ."
    f"sch:title rdfs:domain sch:News ."
    f"sch:title rdfs:range xsd:string ."

    f"sch:content rdf:type owl:DatatypeProperty ."
    f"sch:content rdfs:domain sch:News ."
    f"sch:content rdfs:range xsd:string ."

    f"sch:author rdf:type owl:DatatypeProperty ."
    f"sch:author rdfs:domain sch:News ."
    f"sch:author rdfs:range xsd:string ."

    f"sch:publishedAt rdf:type owl:DatatypeProperty ."
    f"sch:publishedAt rdfs:domain sch:News ."
    f"sch:publishedAt rdfs:range xsd:dateTime ."

    f"sch:sourceURL rdf:type owl:DatatypeProperty ."
    f"sch:sourceURL rdfs:domain sch:News ."
    f"sch:sourceURL rdfs:range xsd:anyURI ."
)

# ============================================================
# 3. NEWS
# ============================================================

for _, row in news_df.iterrows():

    news = iri(row["idNews"])

    triples.append(
        f"{news} rdf:type sch:News ."
    )

    triples.append(
        f"{news} sch:title "
        f"{sparql_literal(row['title'])} ."
    )

    triples.append(
        f"{news} sch:content "
        f"{sparql_literal(row['content'])} ."
    )

    triples.append(
        f"{news} sch:author "
        f"{sparql_literal(row['author'])} ."
    )

    published_at = datetime_literal(row["publishedAt"])

    if published_at:
        triples.append(
            f"{news} sch:publishedAt {published_at} ."
        )

    if not pd.isna(row["sourceURL"]):

        source_url = str(row["sourceURL"]).strip()

        if source_url:

            triples.append(
                f'{news} sch:sourceURL '
                f'"{source_url}"^^xsd:anyURI .'
            )

    # --------------------------------------------------------
    # hasStatement
    # --------------------------------------------------------

    if not pd.isna(row["hasStatement"]):

        statements = str(row["hasStatement"]).split(",")

        for statement_id in statements:

            statement_id = statement_id.strip()

            if statement_id:

                triples.append(
                    f"{news} sch:hasStatement "
                    f"{iri(statement_id)} ."
                )

# ============================================================
# 4. PERSON
# ============================================================

for _, row in person_df.iterrows():

    # ========================================================
    # ID PERSON MENJADI IRI INDIVIDUAL
    # Contoh:
    # P0001 -> data:P0001
    # ========================================================

    person = iri(row["idPerson"])

    # ========================================================
    # INSTANCE DARI CLASS Person
    # ========================================================

    triples.append(
        f"{person} rdf:type sch:Person ."
    )

    # ========================================================
    # DATA PROPERTY personName
    # ========================================================

    if not pd.isna(row["personName"]):

        triples.append(
            f"{person} sch:personName "
            f"{sparql_literal(row['personName'])} ."
        )



# ============================================================
# 5. STATEMENT
# ============================================================

for _, row in statement_df.iterrows():

    statement = iri(row["idStatement"])

    triples.append(
        f"{statement} rdf:type sch:Statement ."
    )

    # textStatement
    if not pd.isna(row["textStatement"]):

        triples.append(
            f"{statement} sch:textStatement "
            f"{sparql_literal(row['textStatement'])} ."
        )

    # madeBy
    if not pd.isna(row["madeBy"]):

        person = iri(row["madeBy"])

        triples.append(
            f"{statement} sch:madeBy {person} ."
        )

        # Person otomatis dibuat sebagai individual Person
        triples.append(
            f"{person} rdf:type sch:Person ."
        )

    # expressStance
    if not pd.isna(row["expressStance"]):

        stance = iri(row["expressStance"])

        triples.append(
            f"{statement} sch:expressesStance "
            f"{stance} ."
        )


# ============================================================
# 6. STANCE
# ============================================================

for _, row in stance_df.iterrows():

    stance = iri(row["idStance"])

    triples.append(
        f"{stance} rdf:type sch:Stance ."
    )

    if not pd.isna(row["hasStanceType"]):

        stance_type = iri(row["hasStanceType"])

        triples.append(
            f"{stance} sch:hasStanceType "
            f"{stance_type} ."
        )


# ============================================================
# 7. STANCE TYPE
# ============================================================

for _, row in stance_type_df.iterrows():

    stance_type = iri(row["idStanceType"])

    triples.append(
        f"{stance_type} rdf:type sch:StanceType ."
    )

# ============================================================
# MEMBUAT QUERY INSERT DATA
# ============================================================

sparql_query = PREFIX + "\nINSERT DATA {\n"

for triple in triples:

    sparql_query += "    " + triple + "\n"

sparql_query += "}\n"


# ============================================================
# SIMPAN QUERY UNTUK DEBUGGING
# ============================================================

with open(
    "import_political_ontology.sparql",
    "w",
    encoding="utf-8"
) as f:

    f.write(sparql_query)


print()
print("Jumlah triple:", len(triples))
print("Query disimpan sebagai:")
print("import_political_ontology.sparql")


# ============================================================
# KIRIM KE GRAPHDB
# ============================================================

headers = {
    "Content-Type": "application/sparql-update"
}

response = requests.post(
    SPARQL_ENDPOINT,
    data=sparql_query.encode("utf-8"),
    headers=headers
)


# ============================================================
# HASIL
# ============================================================

print()
print("HTTP Status:", response.status_code)

if response.ok:

    print("======================================")
    print("IMPORT BERHASIL")
    print("======================================")

else:

    print("======================================")
    print("IMPORT GAGAL")
    print("======================================")

    print(response.text)