"""
Astro Pi Mission Space Lab 2026/27
==================================

Titre du projet
---------------
Fusion de capteurs et vision : deux methodes independantes pour estimer les
mouvements d'un systeme spatial.

Question scientifique
---------------------
Peut-on estimer les rotations de l'Astro Pi a bord de l'ISS en combinant les
capteurs inertiels, puis verifier cette estimation independamment grace au
mouvement apparent observe dans les images de la Terre ?

Hypothese
---------
Le gyroscope est le capteur le plus utile pour mesurer les variations rapides
de rotation, mais il peut deriver avec le temps. Le magnetometre peut apporter
une reference lente de direction, mais il est sensible aux perturbations et au
champ magnetique terrestre qui varie le long de l'orbite. L'accelerometre peut
detecter des accelerations ou des etats suspects, mais il ne doit pas etre
traite comme une verticale parfaite dans l'ISS, car l'environnement est en
microgravite.

La camera ne mesure pas exactement la meme grandeur que l'IMU. Elle observe un
mouvement apparent dans l'image, qui melange rotation de la camera, mouvement
orbital de l'ISS, relief, nuages, perspective, luminosite et qualite des
points visuels. Elle est donc utilisee comme verification independante, pas
comme verite absolue.

Idee centrale
-------------
Le programme construit une petite chaine de mesure scientifique :

1. Il mesure l'IMU avec le Sense HAT :
   - gyroscope : vitesse angulaire ;
   - accelerometre : acceleration mesuree sur les trois axes ;
   - magnetometre : direction et intensite du champ magnetique.

2. Il estime la rotation avec les capteurs inertiels :
   - integration du gyroscope sur l'intervalle entre deux cycles ;
   - propagation d'une attitude 3D sous forme de quaternion ;
   - conversion en angles roll, pitch et yaw pour faciliter l'analyse ;
   - correction lente avec le changement de cap magnetique ;
   - score de qualite accelerometre ;
   - score de qualite magnetometre.

3. Il capture une image de la Terre avec la camera.

4. Il compare deux images successives avec OpenCV :
   - detection de points caracteristiques ORB ;
   - appariement des points entre les deux images ;
   - estimation d'une transformation affine partielle ;
   - extraction d'une rotation visuelle et d'un decalage en pixels.

5. Il compare deux estimations independantes :
   - rotation inertielle estimee pendant l'intervalle ;
   - rotation apparente mesuree entre les deux images.

Ce que le programme cherche a prouver
-------------------------------------
Le but n'est pas de dire "ce capteur a raison" ou "la camera a raison". Une
conclusion plus solide est :

- les deux methodes sont compatibles ;
- les deux methodes sont moyennement compatibles ;
- les deux methodes divergent, et cette divergence peut etre expliquee par
  la derive, le manque de points visuels, les nuages, la perspective, le champ
  magnetique ou le mouvement orbital.

Cette approche est interessante pour Mission Space Lab parce que les donnees
collectees sont directement liees a la question scientifique. Les capteurs
servent a estimer le mouvement, et les photos servent a verifier cette
estimation. La camera n'est donc pas decorative : elle est indispensable a
l'investigation.

Pourquoi plusieurs capteurs ?
-----------------------------
Gyroscope seul :
Le gyroscope mesure une vitesse angulaire. En multipliant cette vitesse par le
temps ecoule, on obtient une variation d'angle. C'est tres efficace sur des
intervalles courts, mais une petite erreur constante cree une derive si on
integre pendant longtemps.

Accelerometre + gyroscope :
Sur Terre, l'accelerometre aide souvent a retrouver la direction de la gravite.
Dans l'ISS, cette interpretation est plus fragile. Le programme l'utilise donc
comme un indicateur de qualite et d'anomalie plutot que comme une reference
absolue d'orientation.

Magnetometre + gyroscope :
Le magnetometre fournit une direction liee au champ magnetique. Il peut aider a
reduire la derive du gyroscope, mais il peut aussi etre perturbe. Le programme
applique donc une correction faible, volontairement prudente.

Fusion des trois :
La fusion utilise le gyroscope pour la dynamique rapide, le magnetometre comme
correction lente, et l'accelerometre comme diagnostic. C'est une version simple
et robuste d'une logique de navigation embarquee.

Attitude quaternion :
Le programme maintient aussi une estimation 3D de l'attitude sous forme de
quaternion. Les quaternions evitent plusieurs problemes des angles d'Euler,
notamment les singularites lorsque les rotations s'enchainent. Les angles
roll, pitch et yaw sont quand meme sauvegardes dans le CSV car ils sont plus
faciles a lire apres la mission.

Camera :
La camera fournit une estimation independante. Elle ne voit pas directement la
rotation du boitier, mais elle observe le mouvement apparent des elements dans
l'image. Si l'IMU estime une rotation compatible avec l'image, la confiance
augmente.

Diagnostic d'anomalie
---------------------
Le programme peut signaler plusieurs situations :

- no_sense_hat : les capteurs Sense HAT ne sont pas disponibles ;
- no_camera : la camera n'est pas disponible ;
- gyro_outlier : vitesse angulaire tres elevee ;
- accel_outlier : acceleration totale trop elevee ;
- microgravity_or_low_accel : acceleration totale tres faible ;
- mag_outlier : champ magnetique hors intervalle attendu ;
- vision_no_features : pas assez de points visuels ;
- vision_few_matches : trop peu d'appariements entre deux images ;
- vision_transform_failed : transformation visuelle impossible ;
- strong_coherence : IMU et vision tres compatibles ;
- medium_coherence : compatibilite moyenne ;
- weak_coherence : divergence importante ;
- vision_unavailable : comparaison visuelle impossible sur ce cycle ;
- imu_unavailable : donnees IMU indisponibles.

Le diagnostic ne remplace pas l'analyse scientifique. Il cree une trace
objective pour savoir quelles parties des donnees sont fiables et quelles
parties doivent etre interpretees avec prudence.

Score de confiance
------------------
Le programme calcule plusieurs scores :

- sensor_health_score : qualite interne des capteurs, fondee sur les limites
  physiques simples et sur une detection statistique glissante ;
- vision_confidence : confiance dans l'estimation visuelle, fondee sur le
  nombre de points apparies et le deplacement estime ;
- coherence_score : accord entre la rotation inertielle et la rotation visuelle ;
- mission_confidence : combinaison ponderee des trois scores precedents.

Ce systeme cree une sorte de "boite noire" miniature : il ne se contente pas
de collecter des valeurs, il evalue aussi la credibilite des valeurs.

Fusion adaptive
---------------
La correction magnetometre n'a pas un poids fixe. Le programme ajuste son poids
en fonction de la qualite du magnetometre, de l'etat de l'accelerometre et de
la taille du saut de cap observe. Si le magnetometre devient suspect, le
gyroscope garde presque tout le controle. Si le magnetometre est stable, il
peut corriger davantage la derive lente.

Qualite image
-------------
Chaque image est aussi resumee par trois mesures :

- luminosite moyenne ;
- contraste ;
- nettete estimee par variance du Laplacien.
- complexite visuelle estimee par densite de contours.

Ces valeurs aident a expliquer pourquoi la vision marche bien sur certains
cycles et moins bien sur d'autres. Une image sombre, uniforme ou floue peut
donner peu de points caracteristiques, donc une verification visuelle faible.

Filtre d'innovation
-------------------
Le programme calcule une innovation : l'ecart entre ce que l'IMU predit et ce
que la camera observe. Cet ecart est normalise par une incertitude estimee a
partir de la confiance vision et de la sante capteurs. Cela donne un
innovation_score et un etat de vol simplifie :

- green : donnees coherentes et confiance elevee ;
- yellow : donnees utilisables mais prudence necessaire ;
- red : donnees incompletes ou divergence forte.

Estimation probabiliste
-----------------------
Une couche supplementaire propage une covariance simplifiee de la rotation. La
covariance augmente quand le mouvement est plus fort ou quand la sante capteur
diminue. Quand la camera fournit une mesure visuelle exploitable, le programme
calcule une variance vision, un gain de correction de type Kalman scalaire, une
rotation posterieure et une probabilite d'accord. Cette approche ne transforme
pas l'experience en systeme de navigation certifie, mais elle donne une facon
rigoureuse de dire : "notre estimation est plus ou moins incertaine".

Niveau de risque
----------------
Le champ risk_level resume la situation en quatre categories :

- low : donnees coherentes, accord probable ;
- medium : donnees exploitables avec prudence ;
- high : divergence importante ou incertitude elevee ;
- critical : source principale manquante.

Valeur scientifique
-------------------
Le programme calcule aussi une valeur scientifique par cycle. Cette valeur
combine l'observabilite visuelle, la redondance entre sources, la confiance de
mission et la probabilite d'accord. Le champ decision_code indique ensuite si
la ligne doit etre traitee comme echantillon prioritaire, echantillon utilisable
ou echantillon a revoir. Cela permet de trier rapidement les donnees apres la
mission sans perdre la trace des cas difficiles.

Fichiers produits
-----------------
data.csv
    Une ligne par cycle. Ce fichier contient les mesures brutes, les rotations
    estimees, les scores de qualite, la rotation visuelle et les diagnostics.
    Il est ecrit ligne par ligne avec buffering=1 afin de limiter la perte de
    donnees si le programme s'arrete brutalement.

summary.json
    Resume final de l'experience : nombre de lignes, nombre d'images, score
    moyen de coherence, calibration du gyroscope et interpretation.

calibration.json
    Biais moyen du gyroscope estime au debut de l'execution. Ce biais est
    soustrait aux mesures suivantes pour reduire la derive.

mission.log
    Journal d'evenements et d'erreurs gerees. Il permet de comprendre ce qui
    s'est passe si une lecture de capteur ou une analyse d'image echoue.

img_XXX.jpg
    Images conservees pour permettre la verification visuelle et l'analyse
    OpenCV. Le programme limite volontairement leur nombre.

Contraintes Mission Space Lab
-----------------------------
Le programme respecte les contraintes importantes :

- point d'entree appele main.py ;
- pas de reseau ;
- pas de socket ;
- pas de subprocess ;
- pas d'appel de commande systeme ;
- pas de demande d'interaction utilisateur ;
- pas d'utilisation de la matrice LED ;
- fichiers crees a cote de main.py via __file__ ;
- moins de 42 images conservees ;
- arret avant la limite officielle de 10 minutes.

Mode test actuel
----------------
Les constantes ci-dessous sont reglees pour un test court d'environ une minute :

- TIME_LIMIT_S = 60 ;
- STOP_AFTER_S = 55 ;
- CYCLE_S = 10 ;
- MAX_IMAGES_KEPT = 6.

Pour la version finale ISS, il faudra revenir a un reglage proche de :

- TIME_LIMIT_S = 600 ;
- STOP_AFTER_S = 555 ;
- CYCLE_S = 30 ;
- MAX_IMAGES_KEPT = 20.

Limites scientifiques
---------------------
Le programme ne pretend pas determiner une orientation absolue parfaite de
l'Astro Pi. Ce serait trop ambitieux avec seulement quelques minutes de donnees
et sans modele complet de l'orbite, de l'attitude de l'ISS, de la geometrie de
la camera et de la scene observee.

Il produit plutot une experience robuste :

- mesurer ;
- estimer ;
- verifier ;
- signaler les anomalies ;
- garder les preuves dans des fichiers analysables.

Cette prudence est une force. Une bonne experience spatiale ne consiste pas a
pretendre que tout est certain. Elle consiste a quantifier la confiance dans les
mesures et a expliquer clairement les cas ou les capteurs ne racontent pas la
meme histoire.
"""

import csv
import json
import logging
import math
import time
from pathlib import Path

START = time.monotonic()

try:
    from picamzero import Camera
except Exception:
    Camera = None

try:
    from sense_hat import SenseHat
except Exception:
    SenseHat = None

try:
    import cv2
except Exception:
    cv2 = None

try:
    import numpy as np
except Exception:
    np = None

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None


BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "data.csv"
SUMMARY_PATH = BASE_DIR / "summary.json"
LOG_PATH = BASE_DIR / "mission.log"
CALIBRATION_PATH = BASE_DIR / "calibration.json"
REPORT_PATH = BASE_DIR / "mission_report.txt"
VISUAL_SUMMARY_PATH = BASE_DIR / "summary_visual.png"

TIME_LIMIT_S = 60
STOP_AFTER_S = 55
CYCLE_S = 10
MAX_IMAGES_KEPT = 6
CALIBRATION_SAMPLES = 12
CALIBRATION_PAUSE_S = 0.15

GYRO_DEG_S_LIMIT = 500.0
ACCEL_G_LIMIT = 8.0
MAG_UT_MIN = 5.0
MAG_UT_MAX = 120.0
GYRO_RAW_TO_DEG_S = 180.0 / math.pi
GYRO_WEIGHT = 0.98
MAG_WEIGHT = 0.02
HEALTH_WINDOW = 8
ANOMALY_Z_LIMIT = 3.5
MIN_ADAPTIVE_MAG_WEIGHT = 0.005
MAX_ADAPTIVE_MAG_WEIGHT = 0.08
BASE_PROCESS_NOISE_DEG2 = 0.04
BASE_VISION_NOISE_DEG2 = 4.0
MAX_COVARIANCE_DEG2 = 900.0
FLIGHT_GREEN_MISSION_CONFIDENCE = 0.72
FLIGHT_GREEN_INNOVATION_SCORE = 0.70
FLIGHT_YELLOW_MISSION_CONFIDENCE = 0.45
FLIGHT_YELLOW_INNOVATION_SCORE = 0.40
RISK_HIGH_COVARIANCE_DEG2 = 120.0
RISK_LOW_AGREEMENT_PROBABILITY = 0.65
RISK_HIGH_AGREEMENT_PROBABILITY = 0.25
SCIENCE_PRIORITY_SCORE = 0.75
SCIENCE_USABLE_SCORE = 0.45
IMAGE_DARK_LIMIT = 20.0
IMAGE_OVEREXPOSED_LIMIT = 235.0
IMAGE_LOW_CONTRAST_LIMIT = 8.0
IMAGE_BLUR_LIMIT = 15.0
IMAGE_LOW_COMPLEXITY_LIMIT = 0.01
VISION_MIN_MATCHES = 12
VISION_MIN_INLIERS = 8


CSV_FIELDS = [
    "timestamp_s",
    "image",
    "gyro_x_dps",
    "gyro_y_dps",
    "gyro_z_dps",
    "accel_x_g",
    "accel_y_g",
    "accel_z_g",
    "accel_total_g",
    "mag_x_ut",
    "mag_y_ut",
    "mag_z_ut",
    "mag_total_ut",
    "gyro_step_x_deg",
    "gyro_step_y_deg",
    "gyro_step_z_deg",
    "gyro_step_total_deg",
    "quat_w",
    "quat_x",
    "quat_y",
    "quat_z",
    "roll_deg",
    "pitch_deg",
    "yaw_deg",
    "gyro_rotation_deg",
    "mag_heading_deg",
    "gyro_mag_heading_delta_deg",
    "fused_step_z_deg",
    "fused_rotation_deg",
    "adaptive_gyro_weight",
    "adaptive_mag_weight",
    "accel_orientation_quality",
    "mag_quality",
    "gyro_noise_index",
    "accel_noise_index",
    "mag_noise_index",
    "vision_rotation_deg",
    "vision_shift_px",
    "vision_matches",
    "vision_confidence",
    "image_brightness",
    "image_contrast",
    "image_sharpness",
    "visual_complexity",
    "visual_rejection_reason",
    "innovation_deg",
    "innovation_sigma",
    "innovation_score",
    "rotation_covariance_deg2",
    "vision_variance_deg2",
    "kalman_gain",
    "posterior_rotation_deg",
    "posterior_covariance_deg2",
    "agreement_probability",
    "consensus_rotation_deg",
    "observability_score",
    "redundancy_score",
    "science_value_score",
    "imu_vision_delta_deg",
    "coherence_score",
    "sensor_health_score",
    "mission_confidence",
    "flight_state",
    "risk_level",
    "decision_code",
    "event_class",
    "flags",
]


def elapsed_s():
    return time.monotonic() - START


def setup_logging():
    logging.basicConfig(
        filename=str(LOG_PATH),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def init_sense_hat():
    if SenseHat is None:
        logging.error("sense_hat library unavailable")
        return None
    try:
        sense = SenseHat()
        # The LED matrix is not used for the experiment.
        return sense
    except Exception as exc:
        logging.error("Sense HAT init failed: %s", exc)
        return None


def init_camera():
    if Camera is None:
        logging.error("picamzero library unavailable")
        return None
    try:
        return Camera()
    except Exception as exc:
        logging.error("Camera init failed: %s", exc)
        return None


def safe_axis(data, key):
    try:
        return float(data.get(key, 0.0))
    except Exception:
        return 0.0


def vector_total(x, y, z):
    return math.sqrt(x * x + y * y + z * z)


def clamp(value, low, high):
    return max(low, min(high, value))


def to_float(value, default=None):
    if value in ("", None):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def round_or_blank(value, digits):
    number = to_float(value)
    if number is None:
        return ""
    return round(number, digits)


def normalize_quaternion(q):
    norm = math.sqrt(sum(part * part for part in q))
    if norm == 0.0:
        return (1.0, 0.0, 0.0, 0.0)
    return tuple(part / norm for part in q)


def multiply_quaternions(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def quaternion_from_rotation_vector(rx_deg, ry_deg, rz_deg):
    angle_deg = vector_total(rx_deg, ry_deg, rz_deg)
    if angle_deg == 0.0:
        return (1.0, 0.0, 0.0, 0.0)
    angle_rad = math.radians(angle_deg)
    half_angle = angle_rad / 2.0
    scale = math.sin(half_angle) / angle_deg
    return normalize_quaternion(
        (
            math.cos(half_angle),
            rx_deg * scale,
            ry_deg * scale,
            rz_deg * scale,
        )
    )


def integrate_attitude(q, rx_deg, ry_deg, rz_deg):
    delta = quaternion_from_rotation_vector(rx_deg, ry_deg, rz_deg)
    return normalize_quaternion(multiply_quaternions(q, delta))


def quaternion_to_euler(q):
    w, x, y, z = q
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        pitch = math.degrees(math.copysign(math.pi / 2.0, sinp))
    else:
        pitch = math.degrees(math.asin(sinp))

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))
    return roll, pitch, yaw


def robust_z_score(value, history):
    numeric_value = to_float(value)
    if numeric_value is None or len(history) < 4:
        return 0.0
    numeric = [to_float(item) for item in history]
    numeric = [item for item in numeric if item is not None]
    if len(numeric) < 4:
        return 0.0
    mean = sum(numeric) / len(numeric)
    variance = sum((item - mean) ** 2 for item in numeric) / len(numeric)
    sigma = math.sqrt(variance)
    if sigma < 1e-9:
        return 0.0
    return abs((numeric_value - mean) / sigma)


def rolling_noise_index(value, history):
    numeric_value = to_float(value)
    if numeric_value is None or len(history) < 4:
        return ""
    numeric = [to_float(item) for item in history]
    numeric = [item for item in numeric if item is not None]
    if len(numeric) < 4:
        return ""
    mean = sum(numeric) / len(numeric)
    variance = sum((item - mean) ** 2 for item in numeric) / len(numeric)
    sigma = math.sqrt(variance)
    scale = max(1.0, abs(mean))
    return clamp(sigma / scale, 0.0, 1.0)


def update_health_history(history, key, value):
    numeric_value = to_float(value)
    if numeric_value is None:
        return
    bucket = history.setdefault(key, [])
    bucket.append(numeric_value)
    if len(bucket) > HEALTH_WINDOW:
        del bucket[0]


def sensor_health_score(row, history, flags):
    checks = [
        ("gyro_step_total_deg", 0.0, 90.0),
        ("accel_total_g", 0.0, ACCEL_G_LIMIT),
        ("mag_total_ut", MAG_UT_MIN, MAG_UT_MAX),
    ]
    score = 1.0
    for key, low, high in checks:
        numeric = to_float(row.get(key, ""))
        if numeric is None:
            score -= 0.20
            continue
        if numeric < low or numeric > high:
            score -= 0.35
        z_score = robust_z_score(numeric, history.get(key, []))
        if z_score > ANOMALY_Z_LIMIT:
            flags.append(f"{key}_statistical_anomaly")
            score -= 0.25

    for key, _, _ in checks:
        update_health_history(history, key, row.get(key, ""))

    return clamp(score, 0.0, 1.0)


def adaptive_mag_weight(mag_q, accel_q, mag_step):
    mag_quality_value = to_float(mag_q)
    mag_step_value = to_float(mag_step)
    if mag_quality_value is None or mag_step_value is None:
        return 0.0
    accel_factor = to_float(accel_q, 0.5)
    quality = clamp(0.75 * mag_quality_value + 0.25 * accel_factor, 0.0, 1.0)
    # Very large heading jumps are treated as suspicious and reduce correction.
    jump_penalty = clamp(abs(mag_step_value) / 45.0, 0.0, 1.0)
    weight = MIN_ADAPTIVE_MAG_WEIGHT + (
        MAX_ADAPTIVE_MAG_WEIGHT - MIN_ADAPTIVE_MAG_WEIGHT
    ) * quality * (1.0 - jump_penalty)
    return clamp(weight, MIN_ADAPTIVE_MAG_WEIGHT, MAX_ADAPTIVE_MAG_WEIGHT)


def image_quality_metrics(image_file):
    if not image_file or cv2 is None or np is None:
        return "", "", "", "", ["image_quality_unavailable"]
    try:
        image = cv2.imread(str(BASE_DIR / image_file), cv2.IMREAD_GRAYSCALE)
        if image is None:
            return "", "", "", "", ["image_quality_read_error"]
        small = cv2.resize(image, None, fx=0.125, fy=0.125)
        brightness = float(np.mean(small))
        contrast = float(np.std(small))
        sharpness = float(cv2.Laplacian(small, cv2.CV_64F).var())
        edges = cv2.Canny(small, 50, 150)
        visual_complexity = float(np.count_nonzero(edges)) / float(edges.size)
        flags = []
        if brightness < IMAGE_DARK_LIMIT:
            flags.append("image_dark")
        if brightness > IMAGE_OVEREXPOSED_LIMIT:
            flags.append("image_overexposed")
        if contrast < IMAGE_LOW_CONTRAST_LIMIT:
            flags.append("image_low_contrast")
        if sharpness < IMAGE_BLUR_LIMIT:
            flags.append("image_blurry_or_uniform")
        if visual_complexity < IMAGE_LOW_COMPLEXITY_LIMIT:
            flags.append("image_low_visual_complexity")
        return brightness, contrast, sharpness, visual_complexity, flags
    except Exception as exc:
        logging.error("Image quality estimation failed: %s", exc)
        return "", "", "", "", ["image_quality_error"]


def innovation_metrics(imu_step, vision_rotation, vision_confidence, sensor_score):
    imu_value = to_float(imu_step)
    vision_value = to_float(vision_rotation)
    if imu_value is None or vision_value is None:
        return "", "", ""
    innovation = abs(angle_delta_deg(imu_value, vision_value))
    vision_uncertainty = 25.0 * (1.0 - to_float(vision_confidence, 0.0))
    sensor_uncertainty = 20.0 * (1.0 - to_float(sensor_score, 0.0))
    sigma = max(2.0, 2.0 + vision_uncertainty + sensor_uncertainty)
    innovation_sigma = innovation / sigma
    score = clamp(1.0 - innovation_sigma / 3.0, 0.0, 1.0)
    return innovation, innovation_sigma, score


def vision_variance(vision_confidence, visual_complexity):
    confidence = to_float(vision_confidence, 0.0)
    complexity = to_float(visual_complexity, 0.0)
    confidence_penalty = (1.0 - confidence) * 30.0
    complexity_penalty = (1.0 - clamp(complexity * 20.0, 0.0, 1.0)) * 20.0
    return BASE_VISION_NOISE_DEG2 + confidence_penalty + complexity_penalty


def propagate_covariance(previous_covariance, gyro_step_total, sensor_score):
    motion = abs(to_float(gyro_step_total, 0.0))
    health = to_float(sensor_score, 0.3)
    process_noise = BASE_PROCESS_NOISE_DEG2 + motion * 0.03 + (1.0 - health) * 8.0
    return clamp(previous_covariance + process_noise, 0.0, MAX_COVARIANCE_DEG2)


def probabilistic_update(predicted_rotation, covariance, vision_rotation, vision_var):
    predicted = to_float(predicted_rotation)
    vision = to_float(vision_rotation)
    if predicted is None or vision is None:
        return "", covariance, 0.0, ""
    covariance = max(to_float(covariance, 1.0), 1e-9)
    vision_var = max(to_float(vision_var, BASE_VISION_NOISE_DEG2), 1e-9)
    gain = covariance / (covariance + vision_var)
    residual = angle_delta_deg(vision, predicted)
    posterior = predicted + gain * residual
    posterior_covariance = (1.0 - gain) * covariance
    normalized_residual = abs(residual) / math.sqrt(covariance + vision_var)
    agreement_probability = math.exp(-0.5 * normalized_residual * normalized_residual)
    return posterior, posterior_covariance, gain, agreement_probability


def flight_state(mission_score, innovation_score, flags):
    if "imu_unavailable" in flags or "vision_unavailable" in flags:
        return "red"
    mission = to_float(mission_score)
    innovation = to_float(innovation_score)
    if mission is None or innovation is None:
        return "yellow"
    if mission >= FLIGHT_GREEN_MISSION_CONFIDENCE and innovation >= FLIGHT_GREEN_INNOVATION_SCORE:
        return "green"
    if mission >= FLIGHT_YELLOW_MISSION_CONFIDENCE and innovation >= FLIGHT_YELLOW_INNOVATION_SCORE:
        return "yellow"
    return "red"


def risk_level(row, flags):
    state = row.get("flight_state", "")
    probability = to_float(row.get("agreement_probability", ""))
    covariance = to_float(row.get("posterior_covariance_deg2", ""))
    if "imu_unavailable" in flags or "vision_unavailable" in flags:
        return "critical"
    if state == "green" and probability is not None and probability > RISK_LOW_AGREEMENT_PROBABILITY:
        return "low"
    if covariance is not None and covariance > RISK_HIGH_COVARIANCE_DEG2:
        return "high"
    if probability is not None and probability < RISK_HIGH_AGREEMENT_PROBABILITY:
        return "high"
    if state == "red":
        return "high"
    return "medium"


def consensus_rotation(row):
    posterior = to_float(row.get("posterior_rotation_deg", ""))
    fused = to_float(row.get("fused_step_z_deg", ""))
    vision = to_float(row.get("vision_rotation_deg", ""))
    probability = to_float(row.get("agreement_probability", ""), 0.0)
    if posterior is not None:
        return posterior
    if fused is not None and vision is not None:
        return (1.0 - probability) * fused + probability * vision
    if fused is not None:
        return fused
    if vision is not None:
        return vision
    return ""


def observability_score(row):
    vision_conf = to_float(row.get("vision_confidence", ""), 0.0)
    complexity = to_float(row.get("visual_complexity", ""), 0.0)
    gyro_motion = to_float(row.get("gyro_step_total_deg", ""), 0.0)
    motion_factor = clamp(gyro_motion / 3.0, 0.0, 1.0)
    complexity_factor = clamp(complexity * 25.0, 0.0, 1.0)
    return clamp(0.45 * vision_conf + 0.35 * complexity_factor + 0.20 * motion_factor, 0.0, 1.0)


def redundancy_score(row):
    keys = (
        "gyro_step_total_deg",
        "mag_quality",
        "accel_orientation_quality",
        "vision_rotation_deg",
    )
    available = sum(to_float(row.get(key, "")) is not None for key in keys)
    return available / float(len(keys))


def science_value_score(row):
    observable = to_float(row.get("observability_score", ""), 0.0)
    redundant = to_float(row.get("redundancy_score", ""), 0.0)
    confidence = to_float(row.get("mission_confidence", ""), 0.0)
    agreement = to_float(row.get("agreement_probability", ""), 0.0)
    return clamp(
        0.30 * observable + 0.25 * redundant + 0.25 * confidence + 0.20 * agreement,
        0.0,
        1.0,
    )


def decision_code(row):
    risk = row.get("risk_level", "")
    science = to_float(row.get("science_value_score", ""), 0.0)
    if risk == "critical":
        return "discard_primary_analysis"
    if risk == "high" and science < SCIENCE_USABLE_SCORE:
        return "review_manually"
    if science >= SCIENCE_PRIORITY_SCORE and risk in ("low", "medium"):
        return "priority_science_sample"
    if science >= SCIENCE_USABLE_SCORE:
        return "usable_science_sample"
    return "low_value_sample"


def classify_event(row, flags):
    confidence = to_float(row.get("mission_confidence", ""))
    coherence = to_float(row.get("coherence_score", ""))
    shift = to_float(row.get("vision_shift_px", ""))
    gyro_total = to_float(row.get("gyro_step_total_deg", ""))

    if "imu_unavailable" in flags:
        return "imu_missing"
    if "vision_unavailable" in flags:
        return "vision_missing"
    if any(("image_dark" in flag or "image_overexposed" in flag) for flag in flags):
        return "image_exposure_limited"
    if any("image_blurry_or_uniform" in flag for flag in flags):
        return "image_sharpness_limited"
    if any(("image_low_contrast" in flag or "image_low_visual_complexity" in flag) for flag in flags):
        return "image_complexity_limited"
    if any(flag in flags for flag in ("vision_few_matches", "vision_few_inliers", "vision_no_features")):
        return "visual_feature_limited"
    if any(flag in flags for flag in ("vision_transform_failed", "vision_transform_invalid")):
        return "visual_transform_limited"
    if confidence is not None and confidence >= 0.75:
        return "validated_motion"
    if coherence is not None and coherence < 0.35:
        return "imu_vision_disagreement"
    if shift is not None and shift > 1200.0:
        return "large_visual_translation"
    if gyro_total is not None and gyro_total < 0.05:
        return "near_stationary"
    if any("statistical_anomaly" in flag for flag in flags):
        return "sensor_statistical_anomaly"
    return "nominal_measurement"


def read_imu(sense):
    flags = []
    values = {
        "gyro_x_dps": "",
        "gyro_y_dps": "",
        "gyro_z_dps": "",
        "accel_x_g": "",
        "accel_y_g": "",
        "accel_z_g": "",
        "accel_total_g": "",
        "mag_x_ut": "",
        "mag_y_ut": "",
        "mag_z_ut": "",
        "mag_total_ut": "",
        "mag_heading_deg": "",
    }
    if sense is None:
        flags.append("no_sense_hat")
        return values, flags

    try:
        gyro = sense.get_gyroscope_raw()
        gx = safe_axis(gyro, "x")
        gy = safe_axis(gyro, "y")
        gz = safe_axis(gyro, "z")
        # Sense HAT raw gyroscope values are angular rates. We convert to
        # degrees per second so they can be compared with visual rotation.
        gx *= GYRO_RAW_TO_DEG_S
        gy *= GYRO_RAW_TO_DEG_S
        gz *= GYRO_RAW_TO_DEG_S
        values["gyro_x_dps"] = gx
        values["gyro_y_dps"] = gy
        values["gyro_z_dps"] = gz
        if max(abs(gx), abs(gy), abs(gz)) > GYRO_DEG_S_LIMIT:
            flags.append("gyro_outlier")
    except Exception as exc:
        logging.error("Gyroscope read failed: %s", exc)
        flags.append("gyro_error")

    try:
        accel = sense.get_accelerometer_raw()
        ax = safe_axis(accel, "x")
        ay = safe_axis(accel, "y")
        az = safe_axis(accel, "z")
        atotal = vector_total(ax, ay, az)
        values["accel_x_g"] = ax
        values["accel_y_g"] = ay
        values["accel_z_g"] = az
        values["accel_total_g"] = atotal
        if atotal > ACCEL_G_LIMIT:
            flags.append("accel_outlier")
        if atotal < 0.02:
            flags.append("microgravity_or_low_accel")
    except Exception as exc:
        logging.error("Accelerometer read failed: %s", exc)
        flags.append("accel_error")

    try:
        mag = sense.get_compass_raw()
        mx = safe_axis(mag, "x")
        my = safe_axis(mag, "y")
        mz = safe_axis(mag, "z")
        mtotal = vector_total(mx, my, mz)
        heading = (math.degrees(math.atan2(my, mx)) + 360.0) % 360.0
        values["mag_x_ut"] = mx
        values["mag_y_ut"] = my
        values["mag_z_ut"] = mz
        values["mag_total_ut"] = mtotal
        values["mag_heading_deg"] = heading
        if mtotal < MAG_UT_MIN or mtotal > MAG_UT_MAX:
            flags.append("mag_outlier")
    except Exception as exc:
        logging.error("Magnetometer read failed: %s", exc)
        flags.append("mag_error")

    return values, flags


def calibrate_gyro(sense):
    if sense is None:
        calibration = {
            "gyro_bias_x_dps": 0.0,
            "gyro_bias_y_dps": 0.0,
            "gyro_bias_z_dps": 0.0,
            "samples": 0,
            "status": "no_sense_hat",
        }
        write_json(CALIBRATION_PATH, calibration)
        return calibration

    samples = []
    for _ in range(CALIBRATION_SAMPLES):
        values, flags = read_imu(sense)
        if not any(flag.endswith("error") for flag in flags):
            gx = to_float(values.get("gyro_x_dps"))
            gy = to_float(values.get("gyro_y_dps"))
            gz = to_float(values.get("gyro_z_dps"))
            if gx is not None and gy is not None and gz is not None:
                samples.append((gx, gy, gz))
        time.sleep(CALIBRATION_PAUSE_S)

    if not samples:
        calibration = {
            "gyro_bias_x_dps": 0.0,
            "gyro_bias_y_dps": 0.0,
            "gyro_bias_z_dps": 0.0,
            "samples": 0,
            "status": "failed",
        }
    else:
        calibration = {
            "gyro_bias_x_dps": sum(sample[0] for sample in samples) / len(samples),
            "gyro_bias_y_dps": sum(sample[1] for sample in samples) / len(samples),
            "gyro_bias_z_dps": sum(sample[2] for sample in samples) / len(samples),
            "samples": len(samples),
            "status": "ok",
        }
    write_json(CALIBRATION_PATH, calibration)
    return calibration


def angle_delta_deg(a, b):
    a_num = to_float(a)
    b_num = to_float(b)
    if a_num is None or b_num is None:
        return ""
    return ((a_num - b_num + 180.0) % 360.0) - 180.0


def capture_photo(camera, image_index):
    if camera is None:
        return "", ["no_camera"]
    filename = f"img_{image_index:03d}.jpg"
    try:
        camera.take_photo(str(BASE_DIR / filename))
        return filename, []
    except Exception as exc:
        logging.error("Photo capture failed: %s", exc)
        return "", ["camera_error"]


def visual_rejection_reason(flags):
    priority = [
        "image_dark",
        "image_overexposed",
        "image_blurry_or_uniform",
        "image_low_contrast",
        "image_low_visual_complexity",
        "vision_few_matches",
        "vision_few_inliers",
        "vision_no_features",
        "vision_transform_failed",
        "vision_transform_invalid",
        "vision_image_read_error",
        "vision_library_missing",
        "vision_waiting_for_pair",
    ]
    for flag in priority:
        if flag in flags:
            return flag
    return ""


def estimate_visual_motion(
    previous_file,
    current_file,
    previous_image_flags=None,
    current_image_flags=None,
):
    previous_image_flags = previous_image_flags or []
    current_image_flags = current_image_flags or []
    if not previous_file or not current_file:
        return "", "", 0, "", "vision_waiting_for_pair", ["vision_waiting_for_pair"]
    if cv2 is None or np is None:
        return "", "", 0, "", "vision_library_missing", ["vision_library_missing"]

    blocking_flags = [
        "image_dark",
        "image_overexposed",
        "image_low_contrast",
        "image_blurry_or_uniform",
        "image_low_visual_complexity",
    ]
    for source_name, source_flags in (
        ("previous", previous_image_flags),
        ("current", current_image_flags),
    ):
        for flag in blocking_flags:
            if flag in source_flags:
                reason = f"{source_name}_{flag}"
                logging.info("Visual pair rejected: %s", reason)
                return "", "", 0, "", reason, [f"vision_rejected_{reason}"]

    try:
        img1 = cv2.imread(str(BASE_DIR / previous_file), cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(str(BASE_DIR / current_file), cv2.IMREAD_GRAYSCALE)
        if img1 is None or img2 is None:
            logging.info("Visual pair rejected: image read error")
            return "", "", 0, "", "vision_image_read_error", ["vision_image_read_error"]

        scale = 0.25
        img1 = cv2.resize(img1, None, fx=scale, fy=scale)
        img2 = cv2.resize(img2, None, fx=scale, fy=scale)

        orb = cv2.ORB_create(nfeatures=700)
        keypoints1, descriptors1 = orb.detectAndCompute(img1, None)
        keypoints2, descriptors2 = orb.detectAndCompute(img2, None)
        if descriptors1 is None or descriptors2 is None:
            logging.info("Visual pair rejected: no ORB features")
            return "", "", 0, "", "vision_no_features", ["vision_no_features"]

        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = matcher.match(descriptors1, descriptors2)
        matches = sorted(matches, key=lambda m: m.distance)[:80]
        if len(matches) < VISION_MIN_MATCHES:
            confidence = clamp(len(matches) / float(VISION_MIN_MATCHES), 0.0, 0.35)
            logging.info(
                "Visual pair rejected: only %s matches (minimum %s)",
                len(matches),
                VISION_MIN_MATCHES,
            )
            return "", "", len(matches), confidence, "vision_few_matches", ["vision_few_matches"]

        points1 = np.float32([keypoints1[m.queryIdx].pt for m in matches])
        points2 = np.float32([keypoints2[m.trainIdx].pt for m in matches])
        transform, inliers = cv2.estimateAffinePartial2D(
            points1,
            points2,
            method=cv2.RANSAC,
            ransacReprojThreshold=4.0,
        )
        if transform is None:
            logging.info("Visual pair rejected: affine transformation failed")
            return "", "", len(matches), 0.0, "vision_transform_failed", ["vision_transform_failed"]

        inlier_count = int(inliers.sum()) if inliers is not None else 0
        if inlier_count < VISION_MIN_INLIERS:
            confidence = clamp(inlier_count / float(VISION_MIN_INLIERS), 0.0, 0.35)
            logging.info(
                "Visual pair rejected: only %s RANSAC inliers (minimum %s)",
                inlier_count,
                VISION_MIN_INLIERS,
            )
            return "", "", inlier_count, confidence, "vision_few_inliers", ["vision_few_inliers"]

        a = to_float(transform[0, 0])
        b = to_float(transform[1, 0])
        tx = to_float(transform[0, 2])
        ty = to_float(transform[1, 2])
        if None in (a, b, tx, ty):
            logging.info("Visual pair rejected: non-numeric affine transformation")
            return "", "", inlier_count, 0.0, "vision_transform_invalid", ["vision_transform_invalid"]

        tx /= scale
        ty /= scale
        rotation = math.degrees(math.atan2(b, a))
        shift = math.sqrt(tx * tx + ty * ty)
        confidence = clamp(
            (inlier_count / 50.0) * (1.0 - min(shift, 2500.0) / 5000.0),
            0.0,
            1.0,
        )
        return rotation, shift, inlier_count, confidence, "", []
    except Exception as exc:
        logging.error("Visual motion estimation failed: %s", exc)
        return "", "", 0, "", "vision_error", ["vision_error"]


def coherence_score(imu_rotation, vision_rotation):
    imu_value = to_float(imu_rotation)
    vision_value = to_float(vision_rotation)
    if imu_value is None or vision_value is None:
        return ""
    delta = angle_delta_deg(imu_value, vision_value)
    delta_value = to_float(delta)
    if delta_value is None:
        return ""
    # 1.0 means excellent agreement, 0.0 means difference >= 30 degrees.
    return max(0.0, 1.0 - abs(delta_value) / 30.0)


def mission_confidence(sensor_score, vision_confidence, coherence):
    parts = []
    weights = []
    sensor_value = to_float(sensor_score)
    vision_value = to_float(vision_confidence)
    coherence_value = to_float(coherence)
    if sensor_value is not None:
        parts.append(sensor_value)
        weights.append(0.45)
    if vision_value is not None:
        parts.append(vision_value)
        weights.append(0.25)
    if coherence_value is not None:
        parts.append(coherence_value)
        weights.append(0.30)
    if not parts:
        return ""
    weighted_sum = sum(value * weight for value, weight in zip(parts, weights))
    return clamp(weighted_sum / sum(weights), 0.0, 1.0)


def accel_orientation_quality(accel_total_g):
    total = to_float(accel_total_g)
    if total is None:
        return ""
    if total < 0.02:
        return 0.0
    if total > ACCEL_G_LIMIT:
        return 0.0
    # Close to 1 g would be ideal on Earth. In orbit this often drops, so this
    # is a diagnostic confidence, not a claim that the accelerometer is wrong.
    return max(0.0, 1.0 - abs(total - 1.0))


def mag_quality(mag_total_ut):
    total = to_float(mag_total_ut)
    if total is None:
        return ""
    if total < MAG_UT_MIN or total > MAG_UT_MAX:
        return 0.0
    centre = (MAG_UT_MIN + MAG_UT_MAX) / 2.0
    half_range = (MAG_UT_MAX - MAG_UT_MIN) / 2.0
    return max(0.0, 1.0 - abs(total - centre) / half_range)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2)


def diagnostic_from_flags(flags, score):
    if "no_sense_hat" in flags or "gyro_error" in flags:
        return "imu_unavailable"
    if "no_camera" in flags or any(flag.startswith("vision_") for flag in flags):
        return "vision_unavailable"
    if score == "":
        return "insufficient_data"
    if score >= 0.75:
        return "strong_coherence"
    if score >= 0.45:
        return "medium_coherence"
    return "weak_coherence"


def write_summary(rows, diagnostics, calibration):
    def numeric_values(key):
        values = []
        for row in rows:
            value = to_float(row.get(key))
            if value is not None:
                values.append(value)
        return values

    scores = numeric_values("coherence_score")
    gyro_total = sum(
        abs(value)
        for value in numeric_values("gyro_step_total_deg")
    )
    vision_values = [abs(value) for value in numeric_values("vision_rotation_deg")]
    health_values = numeric_values("sensor_health_score")
    mission_confidence_values = numeric_values("mission_confidence")
    image_sharpness_values = numeric_values("image_sharpness")
    visual_complexity_values = numeric_values("visual_complexity")
    innovation_values = numeric_values("innovation_deg")
    innovation_score_values = numeric_values("innovation_score")
    agreement_values = numeric_values("agreement_probability")
    kalman_gains = numeric_values("kalman_gain")
    science_values = numeric_values("science_value_score")
    observability_values = numeric_values("observability_score")
    adaptive_mag_weights = numeric_values("adaptive_mag_weight")
    last_attitude = None
    for row in reversed(rows):
        if row.get("roll_deg") not in ("", None):
            last_attitude = {
                "roll_deg": row["roll_deg"],
                "pitch_deg": row["pitch_deg"],
                "yaw_deg": row["yaw_deg"],
                "quaternion": [
                    row["quat_w"],
                    row["quat_x"],
                    row["quat_y"],
                    row["quat_z"],
                ],
            }
            break
    flag_counts = {}
    event_counts = {}
    flight_state_counts = {}
    risk_counts = {}
    decision_counts = {}
    for row in rows:
        for flag in str(row["flags"]).split(";"):
            if flag:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
        event_class = row.get("event_class")
        if event_class:
            event_counts[event_class] = event_counts.get(event_class, 0) + 1
        state = row.get("flight_state")
        if state:
            flight_state_counts[state] = flight_state_counts.get(state, 0) + 1
        risk = row.get("risk_level")
        if risk:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        decision = row.get("decision_code")
        if decision:
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

    summary = {
        "question": (
            "Can inertial sensor fusion estimate Astro Pi rotations, and is this "
            "compatible with independent visual motion measured from images?"
        ),
        "runtime_s": round(elapsed_s(), 2),
        "rows": len(rows),
        "images_kept": len([row for row in rows if row.get("image")]),
        "calibration": calibration,
        "mean_coherence_score": round(sum(scores) / len(scores), 3) if scores else None,
        "mean_sensor_health_score": (
            round(sum(health_values) / len(health_values), 3) if health_values else None
        ),
        "mean_mission_confidence": (
            round(sum(mission_confidence_values) / len(mission_confidence_values), 3)
            if mission_confidence_values
            else None
        ),
        "last_estimated_attitude": last_attitude,
        "mean_image_sharpness": (
            round(sum(image_sharpness_values) / len(image_sharpness_values), 3)
            if image_sharpness_values
            else None
        ),
        "mean_visual_complexity": (
            round(sum(visual_complexity_values) / len(visual_complexity_values), 5)
            if visual_complexity_values
            else None
        ),
        "mean_innovation_deg": (
            round(sum(innovation_values) / len(innovation_values), 3)
            if innovation_values
            else None
        ),
        "mean_innovation_score": (
            round(sum(innovation_score_values) / len(innovation_score_values), 3)
            if innovation_score_values
            else None
        ),
        "mean_agreement_probability": (
            round(sum(agreement_values) / len(agreement_values), 3)
            if agreement_values
            else None
        ),
        "mean_kalman_gain": (
            round(sum(kalman_gains) / len(kalman_gains), 5) if kalman_gains else None
        ),
        "mean_observability_score": (
            round(sum(observability_values) / len(observability_values), 3)
            if observability_values
            else None
        ),
        "mean_science_value_score": (
            round(sum(science_values) / len(science_values), 3) if science_values else None
        ),
        "mean_adaptive_mag_weight": (
            round(sum(adaptive_mag_weights) / len(adaptive_mag_weights), 5)
            if adaptive_mag_weights
            else None
        ),
        "valid_vision_pairs": len(scores),
        "sum_abs_gyro_step_total_deg": round(gyro_total, 3),
        "mean_abs_vision_rotation_deg": (
            round(sum(vision_values) / len(vision_values), 3) if vision_values else None
        ),
        "diagnostic_counts": diagnostics,
        "event_counts": event_counts,
        "flight_state_counts": flight_state_counts,
        "risk_counts": risk_counts,
        "decision_counts": decision_counts,
        "flag_counts": flag_counts,
        "interpretation": (
            "A high coherence score means the rotation estimated from the gyro-based "
            "IMU method is compatible with the image-to-image rotation. A low score "
            "does not prove a sensor is wrong: the camera also sees ISS ground motion, "
            "cloud movement, changing perspective, and feature-matching uncertainty."
        ),
    }
    with open(SUMMARY_PATH, "w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2)
    return summary


def describe_visual_limits(flag_counts):
    explanations = []
    mapping = {
        "image_dark": "certaines images etaient trop sombres pour fournir des points fiables",
        "image_overexposed": "certaines images etaient surexposees",
        "image_blurry_or_uniform": "certaines images etaient floues ou trop uniformes",
        "image_low_visual_complexity": "la scene contenait trop peu de contours exploitables",
        "vision_few_matches": "trop peu de points ont pu etre apparies entre deux images",
        "vision_few_inliers": "trop peu d'appariements ont ete confirmes comme coherents par RANSAC",
        "vision_transform_failed": "la transformation image-a-image n'a pas pu etre estimee",
        "vision_transform_invalid": "la transformation estimee contenait des valeurs non exploitables",
        "vision_waiting_for_pair": "il manquait une paire d'images successives pour comparer la vision",
        "image_quality_unavailable": "la qualite image n'a pas pu etre evaluee dans cet environnement",
        "no_camera": "la camera n'etait pas disponible dans cet environnement de test",
    }
    for flag, explanation in mapping.items():
        count = flag_counts.get(flag, 0)
        if count:
            explanations.append(f"- {explanation} ({count} cycle(s)).")
    if not explanations:
        explanations.append("- aucune limite visuelle majeure n'a ete detectee.")
    return "\n".join(explanations)


def report_value(value):
    if value in (None, ""):
        return "not available"
    return str(value)


def write_report(summary, rows):
    flag_counts = summary.get("flag_counts", {})
    report = f"""Mission Space Lab - Rapport scientifique
========================================

Hypothese
---------
La fusion gyroscope + magnetometre, surveillee par l'accelerometre, doit donner
une estimation de rotation plus robuste que le gyroscope seul. Cette estimation
doit etre compatible avec une mesure independante issue du mouvement apparent
entre deux images, lorsque les images contiennent assez de details.

Methode
-------
Le programme collecte les donnees du gyroscope, de l'accelerometre, du
magnetometre et de la camera. Le gyroscope est calibre au demarrage, puis
integre dans le temps. Le magnetometre corrige faiblement la derive quand sa
qualite est suffisante. La camera est analysee avec des points ORB et une
transformation affine partielle. Les paires trop sombres, floues, peu contrastees,
peu complexes ou avec trop peu d'appariements coherents sont exclues de la
comparaison. Un filtre probabiliste compare ensuite la rotation inertielle et la
rotation visuelle.

Resultats
---------
- lignes de donnees: {report_value(summary.get("rows"))}
- images conservees: {report_value(summary.get("images_kept"))}
- paires visuelles valides: {report_value(summary.get("valid_vision_pairs"))}
- confiance moyenne mission: {report_value(summary.get("mean_mission_confidence"))}
- sante moyenne capteurs: {report_value(summary.get("mean_sensor_health_score"))}
- score scientifique moyen: {report_value(summary.get("mean_science_value_score"))}
- probabilite moyenne d'accord IMU/vision: {report_value(summary.get("mean_agreement_probability"))}

Seuils de decision
------------------
Etat / decision          Regle principale                                      Interpretation
-----------------------  -----------------------------------------------------  ---------------------------------------------
green                    mission >= {FLIGHT_GREEN_MISSION_CONFIDENCE} et innovation >= {FLIGHT_GREEN_INNOVATION_SCORE}       confiance et coherence elevees
yellow                   mission >= {FLIGHT_YELLOW_MISSION_CONFIDENCE} et innovation >= {FLIGHT_YELLOW_INNOVATION_SCORE}      cas intermediaire, interpretation prudente
red                      seuils precedents non atteints                         divergence forte ou donnees insuffisantes
low risk                 green et accord > {RISK_LOW_AGREEMENT_PROBABILITY}                           accord probabiliste eleve
high risk                covariance > {RISK_HIGH_COVARIANCE_DEG2} ou accord < {RISK_HIGH_AGREEMENT_PROBABILITY}            incertitude ou divergence importante
priority_science_sample  science_value >= {SCIENCE_PRIORITY_SCORE}                             echantillon prioritaire pour l'analyse
usable_science_sample    science_value >= {SCIENCE_USABLE_SCORE}                             echantillon exploitable
review_manually          risque eleve + science_value < {SCIENCE_USABLE_SCORE}              besoin d'analyse humaine

Limites
-------
Les divergences ne sont pas considerees comme des defauts du programme. Elles
peuvent venir du mouvement orbital de l'ISS, des nuages, du relief, de la
perspective, de la luminosite, du flou, ou d'un faible nombre de points visuels.

Diagnostics visuels
-------------------
{describe_visual_limits(flag_counts)}

Conclusion
----------
Le projet mesure une rotation par deux methodes independantes: inertielle et
visuelle. Quand les scores sont eleves, les deux methodes se soutiennent
mutuellement. Quand les scores sont faibles, le programme conserve les donnees
mais explique pourquoi elles doivent etre interpretees avec prudence. Le point
fort du projet est donc la qualite de l'interpretation, pas seulement la
quantite d'images ou de mesures.
"""
    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        report_file.write(report)


def plot_series(axis, rows, key, label):
    xs, ys = [], []
    for row in rows:
        x = to_float(row.get("timestamp_s"))
        y = to_float(row.get(key))
        if x is not None and y is not None:
            xs.append(x)
            ys.append(y)
    if xs:
        axis.plot(xs, ys, marker="o", linewidth=1.5)
    axis.set_title(label)
    axis.set_xlabel("time (s)")
    axis.grid(True, alpha=0.3)


def write_visual_summary(rows, summary):
    if plt is not None:
        try:
            figure, axes = plt.subplots(2, 2, figsize=(10, 7))
            plot_series(axes[0][0], rows, "coherence_score", "Coherence IMU / vision")
            plot_series(axes[0][1], rows, "vision_confidence", "Visual confidence")
            plot_series(axes[1][0], rows, "sensor_health_score", "Sensor health")

            axes[1][1].axis("off")
            table_rows = [
                ["rows", summary.get("rows")],
                ["valid vision pairs", summary.get("valid_vision_pairs")],
                ["mean mission confidence", summary.get("mean_mission_confidence")],
                ["mean science value", summary.get("mean_science_value_score")],
                ["mean agreement probability", summary.get("mean_agreement_probability")],
            ]
            axes[1][1].table(cellText=table_rows, colLabels=["metric", "value"], loc="center")
            axes[1][1].set_title("Global results")

            figure.tight_layout()
            figure.savefig(str(VISUAL_SUMMARY_PATH), dpi=120)
            plt.close(figure)
            return
        except Exception as exc:
            logging.error("Matplotlib visual generation failed: %s", exc)

    if Image is None or ImageDraw is None:
        logging.warning("No plotting backend available; summary visual not generated")
        return

    try:
        image = Image.new("RGB", (1000, 700), "white")
        draw = ImageDraw.Draw(image)
        draw.text((30, 25), "Mission Space Lab - Summary Visual", fill="black")
        panels = [
            (30, 70, 470, 300, "coherence_score", "Coherence"),
            (530, 70, 970, 300, "vision_confidence", "Visual confidence"),
            (30, 360, 470, 630, "sensor_health_score", "Sensor health"),
        ]
        for left, top, right, bottom, key, title in panels:
            draw.rectangle((left, top, right, bottom), outline="black")
            draw.text((left + 10, top + 10), title, fill="black")
            points = []
            values = []
            for row in rows:
                x = to_float(row.get("timestamp_s"))
                y = to_float(row.get(key))
                if x is not None and y is not None:
                    values.append((x, clamp(y, 0.0, 1.0)))
            if values:
                min_x = min(x for x, _ in values)
                max_x = max(x for x, _ in values)
                span_x = max(1.0, max_x - min_x)
                for x, y in values:
                    px = left + 30 + int((x - min_x) / span_x * (right - left - 60))
                    py = bottom - 30 - int(y * (bottom - top - 70))
                    points.append((px, py))
                if len(points) > 1:
                    draw.line(points, fill="blue", width=3)
                for point in points:
                    draw.ellipse((point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3), fill="blue")
            else:
                draw.text((left + 10, top + 40), "not available", fill="gray")

        table_x, table_y = 540, 370
        draw.text((table_x, table_y), "Global results", fill="black")
        table_rows = [
            ("rows", summary.get("rows")),
            ("valid vision pairs", summary.get("valid_vision_pairs")),
            ("mean mission confidence", summary.get("mean_mission_confidence")),
            ("mean science value", summary.get("mean_science_value_score")),
            ("mean agreement probability", summary.get("mean_agreement_probability")),
        ]
        for index, (label, value) in enumerate(table_rows):
            y = table_y + 35 + index * 35
            draw.text((table_x, y), f"{label}: {report_value(value)}", fill="black")
        image.save(str(VISUAL_SUMMARY_PATH))
    except Exception as exc:
        logging.error("Pillow visual generation failed: %s", exc)


def main():
    setup_logging()
    logging.info("Mission started")

    sense = init_sense_hat()
    camera = init_camera()
    calibration = calibrate_gyro(sense)
    rows = []
    diagnostic_counts = {}
    previous_image = ""
    previous_image_quality_flags = []
    previous_time = elapsed_s()
    cumulative_gyro_z = 0.0
    fused_rotation = 0.0
    previous_mag_heading = ""
    attitude = (1.0, 0.0, 0.0, 0.0)
    health_history = {}
    rotation_covariance = 1.0

    with open(CSV_PATH, "w", newline="", encoding="utf-8", buffering=1) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()

        image_index = 0
        cycle_index = 0
        while elapsed_s() < STOP_AFTER_S and cycle_index < MAX_IMAGES_KEPT:
            cycle_start = elapsed_s()
            row = {field: "" for field in CSV_FIELDS}
            row["timestamp_s"] = round(cycle_start, 3)

            imu, flags = read_imu(sense)
            row.update(imu)

            now = elapsed_s()
            dt = max(0.0, now - previous_time)
            previous_time = now
            gyro_step = 0.0
            gyro_step_x = 0.0
            gyro_step_y = 0.0
            gyro_step_z = 0.0
            raw_gyro_x = to_float(row.get("gyro_x_dps"))
            raw_gyro_y = to_float(row.get("gyro_y_dps"))
            raw_gyro_z = to_float(row.get("gyro_z_dps"))
            bias_x = to_float(calibration.get("gyro_bias_x_dps"), 0.0)
            bias_y = to_float(calibration.get("gyro_bias_y_dps"), 0.0)
            bias_z = to_float(calibration.get("gyro_bias_z_dps"), 0.0)
            gyro_available = (
                raw_gyro_x is not None
                and raw_gyro_y is not None
                and raw_gyro_z is not None
            )
            if gyro_available:
                gyro_x = raw_gyro_x - bias_x
                gyro_y = raw_gyro_y - bias_y
                gyro_z = raw_gyro_z - bias_z
                gyro_step_x = gyro_x * dt
                gyro_step_y = gyro_y * dt
                gyro_step_z = gyro_z * dt
                gyro_step_total = vector_total(gyro_step_x, gyro_step_y, gyro_step_z)
                gyro_step = gyro_step_z
                row["gyro_step_x_deg"] = round(gyro_step_x, 5)
                row["gyro_step_y_deg"] = round(gyro_step_y, 5)
                row["gyro_step_z_deg"] = round(gyro_step_z, 5)
                row["gyro_step_total_deg"] = round(gyro_step_total, 5)
                cumulative_gyro_z += gyro_step_z
                row["gyro_rotation_deg"] = round(cumulative_gyro_z, 5)
                attitude = integrate_attitude(
                    attitude,
                    gyro_step_x,
                    gyro_step_y,
                    gyro_step_z,
                )
                roll, pitch, yaw = quaternion_to_euler(attitude)
                row["quat_w"] = round(attitude[0], 8)
                row["quat_x"] = round(attitude[1], 8)
                row["quat_y"] = round(attitude[2], 8)
                row["quat_z"] = round(attitude[3], 8)
                row["roll_deg"] = round(roll, 5)
                row["pitch_deg"] = round(pitch, 5)
                row["yaw_deg"] = round(yaw, 5)

            mag_step = ""
            current_mag_heading = to_float(row.get("mag_heading_deg"))
            previous_mag_value = to_float(previous_mag_heading)
            if current_mag_heading is not None and previous_mag_value is not None:
                mag_step = angle_delta_deg(current_mag_heading, previous_mag_value)
                mag_step_value = to_float(mag_step)
                if mag_step_value is not None:
                    row["gyro_mag_heading_delta_deg"] = round(abs(mag_step_value), 5)
            if current_mag_heading is not None:
                previous_mag_heading = current_mag_heading

            row["accel_orientation_quality"] = round_or_blank(
                accel_orientation_quality(row.get("accel_total_g")),
                5,
            )
            row["mag_quality"] = round_or_blank(
                mag_quality(row.get("mag_total_ut")),
                5,
            )

            if gyro_available:
                if mag_step != "":
                    mag_w = adaptive_mag_weight(
                        row["mag_quality"],
                        row["accel_orientation_quality"],
                        mag_step,
                    )
                    gyro_w = 1.0 - mag_w
                    fused_step = gyro_w * gyro_step + mag_w * mag_step
                else:
                    mag_w = 0.0
                    gyro_w = 1.0
                    fused_step = gyro_step
                fused_rotation += fused_step
                row["fused_step_z_deg"] = round(fused_step, 5)
                row["fused_rotation_deg"] = round(fused_rotation, 5)
                row["adaptive_gyro_weight"] = round(gyro_w, 5)
                row["adaptive_mag_weight"] = round(mag_w, 5)

            gyro_noise = rolling_noise_index(
                row["gyro_step_total_deg"],
                health_history.get("gyro_step_total_deg", []),
            )
            row["gyro_noise_index"] = round_or_blank(gyro_noise, 5)

            accel_noise = rolling_noise_index(
                row["accel_total_g"],
                health_history.get("accel_total_g", []),
            )
            row["accel_noise_index"] = round_or_blank(accel_noise, 5)

            mag_noise = rolling_noise_index(
                row["mag_total_ut"],
                health_history.get("mag_total_ut", []),
            )
            row["mag_noise_index"] = round_or_blank(mag_noise, 5)

            image_name, image_flags = capture_photo(camera, image_index)
            flags.extend(image_flags)
            row["image"] = image_name

            (
                brightness,
                contrast,
                sharpness,
                visual_complexity,
                quality_flags,
            ) = image_quality_metrics(image_name)
            flags.extend(quality_flags)
            row["image_brightness"] = round_or_blank(brightness, 3)
            row["image_contrast"] = round_or_blank(contrast, 3)
            row["image_sharpness"] = round_or_blank(sharpness, 3)
            row["visual_complexity"] = round_or_blank(visual_complexity, 5)

            (
                rotation,
                shift,
                matches,
                vision_confidence,
                visual_reason,
                vision_flags,
            ) = estimate_visual_motion(
                previous_image,
                image_name,
                previous_image_quality_flags,
                quality_flags,
            )
            flags.extend(vision_flags)
            row["vision_rotation_deg"] = round_or_blank(rotation, 5)
            row["vision_shift_px"] = round_or_blank(shift, 3)
            row["vision_matches"] = matches
            row["vision_confidence"] = round_or_blank(vision_confidence, 5)
            row["visual_rejection_reason"] = (
                visual_reason or visual_rejection_reason(quality_flags + vision_flags)
            )

            score = coherence_score(row["fused_step_z_deg"], row["vision_rotation_deg"])
            row["imu_vision_delta_deg"] = (
                round_or_blank(
                    abs(angle_delta_deg(row["fused_step_z_deg"], row["vision_rotation_deg"])),
                    5,
                )
                if score != ""
                else ""
            )
            row["coherence_score"] = round_or_blank(score, 5)
            row["sensor_health_score"] = round_or_blank(
                sensor_health_score(row, health_history, flags),
                5,
            )
            rotation_covariance = propagate_covariance(
                rotation_covariance,
                row["gyro_step_total_deg"],
                row["sensor_health_score"],
            )
            row["rotation_covariance_deg2"] = round_or_blank(rotation_covariance, 5)
            row["vision_variance_deg2"] = (
                round_or_blank(
                    vision_variance(row["vision_confidence"], row["visual_complexity"]),
                    5,
                )
                if row["vision_confidence"] != ""
                else ""
            )
            posterior, posterior_covariance, gain, agreement_probability = (
                probabilistic_update(
                    row["fused_step_z_deg"],
                    rotation_covariance,
                    row["vision_rotation_deg"],
                    row["vision_variance_deg2"],
                )
            )
            row["kalman_gain"] = round_or_blank(gain, 5)
            row["posterior_rotation_deg"] = round_or_blank(posterior, 5)
            row["posterior_covariance_deg2"] = (
                round_or_blank(posterior_covariance, 5)
                if posterior_covariance != ""
                else round_or_blank(rotation_covariance, 5)
            )
            row["agreement_probability"] = round_or_blank(agreement_probability, 5)
            rotation_covariance = to_float(
                row["posterior_covariance_deg2"],
                rotation_covariance,
            )
            innovation, innovation_sigma, innovation_score = innovation_metrics(
                row["fused_step_z_deg"],
                row["vision_rotation_deg"],
                row["vision_confidence"],
                row["sensor_health_score"],
            )
            row["innovation_deg"] = round_or_blank(innovation, 5)
            row["innovation_sigma"] = round_or_blank(innovation_sigma, 5)
            row["innovation_score"] = round_or_blank(innovation_score, 5)
            final_confidence = mission_confidence(
                row["sensor_health_score"],
                row["vision_confidence"],
                row["coherence_score"],
            )
            row["mission_confidence"] = round_or_blank(final_confidence, 5)
            row["flight_state"] = flight_state(
                row["mission_confidence"],
                row["innovation_score"],
                flags,
            )
            row["risk_level"] = risk_level(row, flags)
            consensus = consensus_rotation(row)
            row["consensus_rotation_deg"] = round_or_blank(consensus, 5)
            row["observability_score"] = round_or_blank(observability_score(row), 5)
            row["redundancy_score"] = round_or_blank(redundancy_score(row), 5)
            row["science_value_score"] = round_or_blank(science_value_score(row), 5)
            row["decision_code"] = decision_code(row)

            diagnostic = diagnostic_from_flags(flags, score)
            diagnostic_counts[diagnostic] = diagnostic_counts.get(diagnostic, 0) + 1
            flags.append(diagnostic)
            row["event_class"] = classify_event(row, flags)
            row["flags"] = ";".join(flags)

            writer.writerow(row)
            rows.append(row)
            logging.info("cycle %s completed: %s", image_index, row["flags"])

            if image_name:
                previous_image = image_name
                previous_image_quality_flags = list(quality_flags)
                image_index += 1
            cycle_index += 1

            sleep_for = CYCLE_S - (elapsed_s() - cycle_start)
            if sleep_for > 0 and elapsed_s() + sleep_for < STOP_AFTER_S:
                time.sleep(sleep_for)

    summary = write_summary(rows, diagnostic_counts, calibration)
    write_report(summary, rows)
    write_visual_summary(rows, summary)
    logging.info("Mission finished")


if __name__ == "__main__":
    main()
