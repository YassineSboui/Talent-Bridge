---
title: Projet Data Jobs -- Objectifs
---

**Nom d'équipe :** Talent-Bridge

**Membres :** Chaime Riahi -- Syrine Kaabi -- Baha salami- Mariem Bouchaala -- Yasine Sboui -- Soulayma Ben Dahsen

**Classe :** 3 ALINFO 7

# Objectif Métier Global

L'objectif est **d'analyser** les offres d'emploi IT afin de **comprendre les tendances du marché** (salaires, métiers, compétences) et d'aider à **la prise de décision** pour les entreprises et les candidats. Le projet permet **d'automatiser** le recrutement (analyse CV, matching), **d'optimiser** les stratégies RH et de **guider** les utilisateurs vers les compétences les plus demandées.

# Les ODD

- 8: Travail decent et croissance economique

- 4: Education de qualite

- 9 : Innovation et infrastructure

# Objectifs BI

|                                                                      |                                                                                                              |                          |
|----------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|--------------------------|
| **Objectif Métier**                                                  | **Objectif BI**                                                                                              | **Technologies**         |
| Optimiser la politique salariale et proposer des salaires équitables | Calculer et comparer les salaires moyens (salary_year_avg) selon métier, pays et remote (job_work_from_home) | **SQL server + PowerBI** |
| Optimiser le recrutement en automatisant le tri des offres           | Identifier la répartition des jobs selon job_schedule_type, job_country et plateforme (job_via)              |                          |
| Optimiser l'orientation des candidats vers les métiers adaptés       | Regrouper les offres selon similarité des caractéristiques (lieu, salaire, type de job)                      |                          |
| Optimiser le recrutement en identifiant les compétences clés         | Extraire et agréger les compétences les plus demandées (job_skills, job_type_skills)                         |                          |
| Maximiser la correspondance entre CV et offres d'emploi              | Calculer la similarité entre profils et offres à partir des skills et du titre (job_title_short)             |                          |
| Minimiser le temps de tri des CV et améliorer la sélection           | Classer les CV/offres selon structures de compétences et catégories de postes (job_title, job_skills)        |                          |

# 

# Objectifs Machine Learning

| **Categorie** | **Objectif ML**             | **Objectif Métier**                                  | **Technologies**         |
|---------------|-----------------------------|------------------------------------------------------|--------------------------|
| ML            | **Prédiction** du salaire   | Estimer salaire à partir des caractéristiques du job | **Regression**           |
| ML            | **Classification** des jobs | Classifier offres ! (remote, full-time...)           | **Classification**       |
| ML            | **Segmentation** des jobs   | Regrouper jobs similaires (clusters)                 | **Clustering** (K-Means) |

# 

# Objectifs NLP

| **Categorie** | **Objectif NLP**                              | **Objectif Métier**                 | **Technologies** |
|---------------|-----------------------------------------------|-------------------------------------|------------------|
| NLP           | **Extraction** & **etection** des compétences | Extraire skills depuis CV et offres | NER, BERT        |
| NLP           | Matching CV ↔ Job Selon **Score**             | Mesurer similarité CV et offre      | Embeddings       |

#   {#section-2}

# Objectifs Deep Learning

| **Categorie** | **Objectif DL**                   | **Objectif Métier**                                | **Technologies** |
|---------------|-----------------------------------|----------------------------------------------------|------------------|
| DL            | **Classification** d'images de CV | Classer CV selon qualité/structure (Pro / Non Pro) | **CNN**          |

score de cv  
amelioration de section de cv llm
