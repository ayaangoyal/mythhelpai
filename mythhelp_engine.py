"""
MYTHhelp AI - engine
--------------------
Databases (health myths + common symptoms) and the keyword-matching logic.
No Streamlit in this file, so it can be tested on its own:

    python mythhelp_engine.py
"""
import re
from difflib import SequenceMatcher

# ---------------------------------------------------------------- sources
SOURCES = {
    "WHO": ("World Health Organization (WHO)", "https://www.who.int"),
    "MOHFW": ("Ministry of Health & Family Welfare, India", "https://www.mohfw.gov.in"),
    "UNICEF": ("UNICEF India", "https://www.unicef.org/india"),
    "NIN": ("ICMR - National Institute of Nutrition", "https://www.nin.res.in"),
    "NACO": ("National AIDS Control Organisation (NACO)", "https://naco.gov.in"),
    "NHS": ("NHS (UK)", "https://www.nhs.uk"),
    "NCI": ("National Cancer Institute (USA)", "https://www.cancer.gov"),
    "CDC": ("US Centers for Disease Control (CDC)", "https://www.cdc.gov"),
    "AAO": ("American Academy of Ophthalmology", "https://www.aao.org"),
    "HARVARD": ("Harvard Health Publishing", "https://www.health.harvard.edu"),
}

# --------------------------------------------------------------- verdicts
VERDICTS = {
    "FALSE": dict(sub="This is a myth", icon="❌", color="#B3261E", bg="#FDECEA",
                  mood="wink", line="Myth busted! Let me explain."),
    "TRUE": dict(sub="This is correct", icon="✅", color="#1B7F46", bg="#E3F5EA",
                 mood="happy", line="Good news. This one is right!"),
    "PARTLY TRUE": dict(sub="Some truth, but not the full story", icon="🌓", color="#1F5FA8",
                        bg="#E6EFFA", mood="think", line="Hmm, this one is a little tricky."),
    "UNVERIFIED": dict(sub="I can't confirm this", icon="🤔", color="#8A5A00", bg="#FFF1CC",
                       mood="think", line="I'm not sure about this one, so let's be careful."),
}


def _m(claim, verdict, kws, why, src):
    return dict(claim=claim, verdict=verdict, kw=[k.strip() for k in kws.split(",")], why=why, src=src)


# ------------------------------------------------------------ myth database
MYTHS = [
    _m("Vaccines cause autism", "FALSE", "vaccine, autism, autistic",
       "Many big studies in many countries found no link between vaccines and autism. Vaccines are checked carefully for safety and they protect children from serious diseases.", "WHO"),
    _m("The COVID-19 vaccine can stop a person from having babies", "FALSE",
       "covid, vaccine, infertility, fertility, pregnant, pregnancy, period, periods, baby",
       "There is no proof that COVID-19 vaccines harm the ability to have children. Health experts have found no such effect in women or men.", "WHO"),
    _m("Garlic protects you from the coronavirus", "FALSE", "garlic, lehsun, covid",
       "Garlic is a healthy food, but there is no proof that eating it protects you from the coronavirus. Wash your hands often and follow your doctor's advice.", "WHO"),
    _m("Antibiotics cure cold, cough and flu", "FALSE", "antibiotic, cold, cough, flu, viral, virus",
       "Colds and flu are caused by tiny germs called viruses. Antibiotics only work on bacteria, which are a different kind of germ. Taking them when not needed can stop them working later, when you really need them.", "WHO"),
    _m("Leftover antibiotics can be used the next time you get a fever", "FALSE",
       "leftover, left over, antibiotic, old medicine, fever, tablet",
       "Antibiotics should be taken only when a doctor prescribes them, in the right dose and for the full time. Using old tablets can hide a serious illness and make germs stronger.", "WHO"),
    _m("Eating well-cooked chicken or eggs gives you bird flu", "FALSE",
       "chicken, egg, bird flu, avian, poultry, murgi",
       "Bird flu spreads mainly from sick birds. Chicken and eggs that are cooked fully are safe to eat. Wash your hands after touching raw meat and keep it away from other food.", "WHO"),
    _m("Malaria comes from drinking dirty water", "FALSE", "malaria, dirty water, mosquito, machhar",
       "Malaria spreads when a certain kind of mosquito bites you. It does not come from the water you drink. Sleep under a mosquito net and do not let water collect near your home.", "WHO"),
    _m("Dengue spreads by touching or sitting near a sick person", "FALSE",
       "dengue, touch, touching, contagious, catching, spread",
       "Dengue spreads through the bite of the Aedes mosquito, not by touch or by breathing the same air. Empty water from coolers, pots and old tyres every week so mosquitoes cannot breed.", "MOHFW"),
    _m("Papaya leaf juice cures dengue", "UNVERIFIED", "papaya, leaf, dengue, platelet",
       "There is not enough strong proof that papaya leaf juice cures dengue. Dengue has no special medicine, so rest, enough fluids and regular checks by a doctor are very important.", "WHO"),
    _m("Cracking your knuckles gives you arthritis", "FALSE", "knuckle, crack, cracking, joint, arthritis",
       "Studies have not found a link between cracking knuckles and arthritis (a joint disease). If your joints hurt or swell, please show a doctor.", "HARVARD"),
    _m("Getting wet in the rain or sitting in cold air gives you a cold", "FALSE",
       "rain, wet, cold weather, cold air, thanda, catch cold, hair wash",
       "Colds are caused by germs called viruses that pass from person to person. Rain or cold air does not make the virus. Cold weather can feel unpleasant, but it is the virus that makes you sick.", "NHS"),
    _m("Eating curd, banana or other cold foods gives you a cold", "FALSE",
       "curd, dahi, banana, cold food, ice cream, cold drink, fridge, thanda",
       "Foods do not give you a cold. Only a virus can. If a food makes your stomach or throat feel bad, you can skip it, but it is not the cause of a cold.", "NHS"),
    _m("Turmeric (haldi) milk can cure cancer", "FALSE", "turmeric, milk, cancer, curcumin, covid",
       "Haldi milk is a warm, tasty drink and turmeric is fine to eat. But no food or drink has been proven to cure cancer. Cancer needs treatment from a cancer doctor.", "NCI"),
    _m("Lemon water or baking soda can cure cancer", "FALSE", "lemon, nimbu, baking soda, soda, cancer",
       "No drink or home remedy has been proven to cure cancer. Using only home remedies can waste precious time. Early treatment by a doctor gives the best chance.", "NCI"),
    _m("Cancer spreads by touching or eating with a patient", "FALSE",
       "cancer, touch, touching, contagious, catching, sharing, spread",
       "Cancer does not spread from person to person like a cold. You can safely hug, touch and eat with someone who has cancer. They need love and support.", "WHO"),
    _m("Eating sweets directly causes diabetes", "PARTLY TRUE", "sweet, mithai, sugar, diabetes, diabetic, cause",
       "Sweets do not directly cause all diabetes. Type 1 diabetes is not caused by sugar. But a lot of sugary food can add extra weight, and extra weight raises the chance of type 2 diabetes. Daily movement and balanced meals help.", "WHO"),
    _m("People with diabetes can never eat fruit or rice", "FALSE", "diabetes, diabetic, fruit, rice, chawal, eat",
       "Most people with diabetes can eat fruit and rice in small, measured amounts as part of a balanced meal. A doctor or dietitian can tell you what is right for you.", "NIN"),
    _m("Insulin is addictive and means your diabetes is very bad", "FALSE", "insulin, addictive, addiction, injection, diabetes",
       "Insulin is something the body makes, and some people need it as medicine. It is not addictive. Needing insulin does not mean you did something wrong. Taking it as the doctor says keeps you safe.", "WHO"),
    _m("If you have no symptoms, your blood pressure must be normal", "FALSE",
       "blood pressure, bp, hypertension, symptom, headache, normal",
       "High blood pressure often gives no signs at all, so it is called a silent problem. The only way to know is to get your blood pressure checked regularly, especially as you grow older.", "WHO"),
    _m("Eating less salt helps keep blood pressure healthy", "TRUE",
       "salt, namak, blood pressure, bp, hypertension, pickle, papad, less salt",
       "Too much salt raises blood pressure. Experts say adults should have less than 5 grams of salt in a day, which is about one level teaspoon. Go easy on pickles, papad and packaged snacks.", "WHO"),
    _m("Washing hands with soap helps stop diarrhoea and many other infections", "TRUE",
       "wash, hand, soap, handwashing, hygiene, germs, diarrhoea",
       "Soap and water remove germs from your hands. Wash for about 20 seconds before eating or feeding a child and after using the toilet. It is one of the cheapest ways to stay healthy.", "UNICEF"),
    _m("ORS drink helps when you have loose motions", "TRUE",
       "ors, oral rehydration, loose motion, diarrhoea, dast, dehydration, zinc",
       "With loose motions, your body loses water and salts. ORS gives them back and stops you from drying out. Children may also need zinc tablets, as the doctor says.", "UNICEF"),
    _m("Babies under 6 months need extra water in summer", "FALSE", "baby, water, summer, hot, heat, 6 months, six months, paani",
       "Breast milk already has all the water a baby needs, even in hot weather. Extra water can make a young baby sick. Feed the baby more often instead.", "UNICEF"),
    _m("Giving a newborn honey, ghutti or gripe water is good for the baby", "FALSE",
       "ghutti, honey, gripe water, janam ghutti, baby, shahad",
       "A newborn should have only the mother's milk. Ghutti, honey or gripe water can carry germs and make the baby sick. Honey is not safe for babies under one year.", "UNICEF"),
    _m("The first yellow milk of a mother (colostrum) is dirty and should be thrown away", "FALSE",
       "colostrum, first milk, yellow milk, breast milk, breastfeeding, throw, dirty",
       "The thick yellow first milk is called colostrum. It is clean and full of things that protect the baby from infections. Start feeding it within the first hour after birth.", "WHO"),
    _m("Feeding only breast milk for the first 6 months is the best start for a baby", "TRUE",
       "breastfeeding, breast milk, breastfeed, exclusive, 6 months, six months, mother milk",
       "For the first 6 months, babies need only breast milk, with no water and no other food. After that, keep breastfeeding and add soft home foods, up to 2 years or more.", "WHO"),
    _m("A pregnant woman must eat double the food", "FALSE",
       "pregnant, pregnancy, eat double, eating for two, double, diet, garbhvati",
       "A pregnant woman does not need to eat double. She needs good food, not just more food: dal, vegetables, fruits, milk or curd, and eggs or other protein if she eats them. Only a little extra is needed in the later months.", "NHS"),
    _m("Iron-folic acid (IFA) tablets in pregnancy harm the baby or make it too big", "FALSE",
       "iron, folic, ifa, tablet, pregnant, pregnancy, blue tablet, red tablet",
       "IFA tablets prevent anaemia (low blood) in mothers and help the baby grow well. They are free at government health centres. If they upset your stomach, tell the ANM or doctor, but do not just stop them.", "MOHFW"),
    _m("Mobile phones cause brain cancer", "UNVERIFIED", "mobile, phone, cell phone, cellphone, radiation, brain, cancer",
       "So far, studies have not proved that mobile phones cause cancer, but scientists are still watching. To be careful, use speaker or earphones for long calls and do not keep the phone by your head while sleeping.", "WHO"),
    _m("Sitting close to the TV or reading in dim light ruins your eyes for life", "FALSE",
       "tv, television, dim light, reading, close, eyes, eyesight",
       "These habits can make your eyes feel tired or dry for a while, but they do not cause lasting damage. Take breaks: every 20 minutes, look at something far away for 20 seconds.", "AAO"),
    _m("Jaggery (gud) is safe for people with diabetes because it is natural", "FALSE",
       "jaggery, gud, gur, diabetes, diabetic, natural, sugar",
       "Jaggery is still a kind of sugar and raises blood sugar just like sugar does. People with diabetes should keep it very small or avoid it, and follow their doctor's advice.", "NIN"),
    _m("Ghee is always bad for your heart", "PARTLY TRUE", "ghee, heart, fat, oil, cholesterol, butter",
       "A small amount of ghee can be part of a healthy diet. Too much fat of any kind, including ghee, can harm the heart and add weight. Eat plenty of vegetables and dal, and walk daily.", "NIN"),
    _m("Heart attacks happen only to old people", "FALSE", "heart attack, heart, young, age, old, cardiac",
       "Heart attacks can happen to younger adults too, especially with smoking, high blood pressure, high sugar, poor sleep or too little exercise. Get regular check-ups.", "WHO"),
    _m("Chest pain is always just gas", "FALSE", "chest pain, chest, gas, acidity, antacid, heart attack, seene mein dard",
       "Chest pain can be gas, but it can also be a heart attack. If the pain is strong or heavy, spreads to the arm or jaw, or comes with sweating or breathlessness, call 108 or 112 right away. Do not wait.", "WHO"),
    _m("Bidis are safer than cigarettes", "FALSE", "bidi, cigarette, safer, tobacco, smoking, smoke",
       "Bidis are not safer. They carry the same dangers and cause cancer, heart disease and lung disease. The best choice is to quit. Free help is available on the national quitline, 1800-11-2356.", "WHO"),
    _m("Chewing tobacco, gutka or khaini is safer than smoking", "FALSE",
       "gutka, khaini, tobacco, chewing, chew, paan masala, zarda, mouth cancer",
       "Chewing tobacco is not safe. It causes mouth cancer and gum disease, and it is very addictive. Free help to quit is available on 1800-11-2356.", "MOHFW"),
    _m("Hookah, shisha or e-cigarettes (vapes) are harmless", "FALSE",
       "hookah, shisha, e cigarette, vape, vaping, harmless",
       "Hookah smoke and vape fumes still carry harmful chemicals. A single hookah session can mean breathing in far more smoke than from one cigarette. They are not a safe choice.", "WHO"),
    _m("Smoking damages the lungs and the heart", "TRUE", "smoking, smoke, cigarette, lung, heart, cancer, harm",
       "Smoking is a leading cause of lung cancer, heart disease and breathing problems. Quitting helps at any age, and the body starts to heal soon after. Free help: 1800-11-2356.", "WHO"),
    _m("TB (tuberculosis) runs in families and is passed down", "FALSE",
       "tb, tuberculosis, hereditary, family, passed down, genes, curse, kshay",
       "TB is not inherited. It spreads through the air when a person with lung TB coughs. TB can be cured with medicines, and they are free at government health centres.", "MOHFW"),
    _m("You can stop TB medicines once you feel better", "FALSE",
       "tb, tuberculosis, medicine, stop, feel better, course",
       "TB germs stay in the body for months, even when you feel well. Stopping early can bring the TB back in a harder form. Take every dose for the full time your doctor says.", "MOHFW"),
    _m("HIV spreads by hugging, shaking hands or sharing food", "FALSE",
       "hiv, aids, hug, hugging, shake hands, sharing food, mosquito, touch",
       "HIV does not spread by hugging, touching, sharing food or mosquito bites. It spreads through certain body fluids: mainly unprotected sex, infected needles, and from mother to baby. People with HIV deserve respect and care.", "NACO"),
    _m("Leprosy (kusht) is a curse and spreads by touch", "FALSE", "leprosy, kusht, kushta, curse, touch, touching",
       "Leprosy is caused by a germ and can be cured with free medicines. It does not spread easily by touch. Treating it early prevents lasting damage, so show a doctor for any pale, numb patch on the skin.", "WHO"),
    _m("Polio drops are unsafe or harmful", "FALSE", "polio, drops, pulse polio, extra dose, infertility, dose",
       "Polio drops are safe and have helped make India polio-free. Extra doses give stronger protection and do not harm children. Every child under 5 should get them each time.", "MOHFW"),
    _m("Measles is a harmless rash and does not need a vaccine", "FALSE", "measles, rash, vaccine, mata, khasra",
       "Measles can be serious. It can cause lung infection, brain swelling and even death in young children. Two doses of the measles vaccine protect children. Take a child with measles to a doctor.", "WHO"),
    _m("Spicy food causes stomach ulcers", "FALSE", "spicy, mirchi, ulcer, stomach, acidity, masala",
       "Most stomach ulcers are caused by a germ called H. pylori or by some painkiller tablets, not by spicy food. Spicy food may upset some stomachs, so eat what suits you.", "NHS"),
    _m("Eating fish and milk together causes white patches on the skin", "FALSE",
       "fish, milk, white patch, leucoderma, vitiligo, safed daag, together, contagious, touch",
       "White patches (vitiligo) are not caused by food mixes like fish and milk. The skin loses its colour because of how the body's defence system works. Vitiligo does not spread by touch.", "NHS"),
    _m("Putting toothpaste, butter or ghee on a burn helps it heal", "FALSE",
       "burn, burnt, toothpaste, butter, ghee, turmeric, ice, scald",
       "These can trap heat and bring germs into the burn. Hold the burn under cool running water for 20 minutes, then cover it loosely with a clean cloth. For a big burn, or a burn on the face or hands, go to a hospital.", "NHS"),
    _m("Cutting a snake bite, tying it tightly or going to a tantrik is the right treatment", "FALSE",
       "snake, snakebite, snake bite, cut, tie, tying, tantrik, ojha, venom, saanp",
       "These can make things worse and waste time. Keep the person calm and the bitten limb still, and rush to a hospital that has anti-snake venom. Call 108 or 112.", "WHO"),
    _m("Giving an iron key, onion, shoe or spoon to someone having a seizure (fit) helps", "FALSE",
       "seizure, fits, epilepsy, mirgi, iron key, onion, shoe, spoon",
       "These do not help and can hurt. Move hard things away, gently turn the person on their side, put something soft under the head and never put anything in the mouth. Call for help if the fit lasts more than 5 minutes.", "NHS"),
    _m("Mental illness is caused by black magic, a curse or a weak mind", "FALSE",
       "mental, depression, anxiety, pagal, black magic, evil, curse, mind, tension",
       "Mental health problems like depression and anxiety are real health conditions, just like diabetes. They can be treated with talking therapy and medicine. Tele-MANAS is a free helpline: call 14416.", "WHO"),
    _m("Boiling water makes it safe to drink", "TRUE",
       "boil, boiled, boiling, water, drinking water, safe water, typhoid, cholera, pani",
       "Boiling kills the germs that cause typhoid, cholera, jaundice and loose motions. Let the water bubble hard for at least a minute, then keep it in a clean, covered pot.", "WHO"),
    _m("Water that looks clear from a tap or borewell is always safe", "FALSE",
       "clear water, tap water, borewell, handpump, clean water, safe, pani",
       "Germs are too tiny to see, so clear water can still make you sick. Boil it, filter it, or treat it with chlorine tablets, and keep it in a clean covered container.", "UNICEF"),
    _m("Sleeping under a mosquito net helps prevent malaria", "TRUE",
       "mosquito net, bed net, net, malaria, sleep, sleeping, machhardani",
       "Malaria mosquitoes bite mostly at night. A mosquito net, especially one treated with medicine, protects you while you sleep. Check it for holes.", "WHO"),
    _m("Walking or exercising about 30 minutes a day keeps your heart healthy", "TRUE",
       "exercise, walking, walk, heart, 30 minutes, physical activity, yoga, fitness, daily",
       "Moving your body most days makes your heart, bones and mood stronger. Adults should aim for at least 150 minutes of brisk activity every week, like walking, cycling or dancing.", "WHO"),
    _m("Sunlight helps your body make vitamin D", "TRUE", "sunlight, sun, vitamin d, vitamin, bones, dhoop, calcium",
       "A short time in gentle sunshine, with arms and legs uncovered, helps your body make vitamin D for strong bones. Do not stay out until your skin burns. A doctor can test your vitamin D if needed.", "NHS"),
    _m("Eating jaggery and beetroot cures anaemia (low blood)", "PARTLY TRUE",
       "anaemia, anemia, jaggery, gud, beetroot, iron, low blood, hemoglobin, haemoglobin, blood",
       "Iron-rich foods such as green leafy vegetables, dal, jaggery and beetroot help, but food alone may not be enough if you already have anaemia. Get a blood test and take the iron tablets your doctor or ANM gives you.", "MOHFW"),
    _m("Putting kajal or surma in a baby's eyes is good for the eyes", "FALSE",
       "kajal, kohl, surma, baby, eyes, eye, anjan",
       "Kajal and surma can carry germs that cause eye infections, and some kinds contain lead, which can harm a baby's brain. Keep a baby's eyes clean with just a clean, wet cloth.", "CDC"),
    _m("A woman is unclean during her period and should not cook, touch pickles or wash her hair", "FALSE",
       "period, menstruation, menstrual, masik, pickle, achar, kitchen, temple, impure, unclean, pad, wash hair",
       "A period is a normal, healthy body process. Nothing about it makes food or the home unclean, and bathing and washing hair are fine. Use clean pads or cloth and change them often.", "UNICEF"),
    _m("Jaundice (peeliya) can be cured by jhaad-phoonk or herbal medicine alone", "FALSE",
       "jaundice, peeliya, jhaad, phoonk, jhad, herbal, liver, yellow eyes, yellow",
       "Jaundice is a sign that something is wrong with the liver or blood. Often it is a liver infection from unsafe water or food. Please see a doctor for tests, drink only safe water and eat light food.", "WHO"),
    _m("Karela, neem or herbal juice can cure diabetes, so you can stop your medicines", "FALSE",
       "karela, neem, diabetes, sugar, herbal, juice, stop medicine, desi",
       "Karela and neem are fine in food, but they have not been proven to replace diabetes medicines. Stopping medicine on your own can push your sugar to dangerous levels. Talk to your doctor before any change.", "WHO"),
    _m("Raw (unboiled) milk is healthier than boiled milk", "FALSE",
       "raw milk, unboiled, boiled milk, boil, milk, dhaar, doodh, healthy",
       "Raw milk can carry germs that cause serious illness, such as TB and brucellosis. Boiling or pasteurising kills these germs, and the milk keeps almost all of its goodness.", "WHO"),
]


# -------------------------------------------------------- symptom database
def _s(name, kws, causes, helps, see):
    return dict(name=name, kw=[k.strip() for k in kws.split(",")],
                causes=causes.split("|"), helps=helps.split("|"), see=see.split("|"))


SYMPTOMS = [
    _s("Itching (itchy skin)", "itch, itching, itchy, khujli, scratch, rash, skin allergy",
       "Dry skin, especially in winter|Mosquito or insect bites|Allergy to a new soap, cream, dust or food|Heat rash from sweat in hot weather|A fungal infection (like ringworm, called daad)|Scabies, which itches most at night and spreads in families",
       "Keep nails short and try not to scratch|Wash with lukewarm water and a mild soap|Put on a plain moisturiser after bathing|Wear loose cotton clothes|Stop any new soap or cream that started it|Wash bedding and clothes in hot water if others at home also itch",
       "It lasts more than 2 weeks or keeps coming back|There are blisters or pus, or the skin looks red, hot and swollen|You also have fever, or yellow skin or eyes|Several people at home are itching|Lips, face or tongue swell, or breathing is hard (call 108 or 112 at once)"),
    _s("Headache", "headache, head ache, sir dard, migraine, head pain, head hurts, head hurt",
       "Not drinking enough water or skipping meals|Poor sleep|Stress or tiredness|Tired eyes from screens or reading|Heat, noise or strong smells|Cold or sinus problems|Migraine, which often hurts on one side",
       "Rest in a quiet, dim room|Drink a glass of water and eat something light|Take short breaks from screens|Sleep at regular times|Gently stretch your neck and shoulders",
       "It is suddenly the worst headache of your life|It comes after a fall or hit on the head|You also have fever and a stiff neck|You feel confused, weak, or have trouble speaking or seeing|You keep vomiting|Headaches keep coming back often"),
    _s("Fever", "fever, bukhar, temperature, high temperature, hot body",
       "Most often a virus, like a cold or flu|Infections that spread in the rainy season, such as dengue, malaria or typhoid|Urine or throat infections|Sometimes after a vaccine (usually mild and short)",
       "Rest and drink plenty of fluids: water, ORS, soups, nimbu pani|Wear light clothes|Eat light food|Wipe the body with a lukewarm, wet cloth|Ask a doctor or pharmacist before giving any medicine, especially to children",
       "Any fever in a baby under 3 months|Fever lasts more than 3 days, or is above 103°F (39.4°C)|There is a rash, very bad headache, stiff neck or trouble breathing|Strong tummy pain, or you keep vomiting|The person is very sleepy, confused, or has a fit|Fever with chills during mosquito season (ask for a dengue or malaria test)"),
    _s("Cough", "cough, coughing, khansi",
       "A cold or other virus|Dust, smoke or pollution|Allergy|Acidity coming up into the throat|Asthma|Smoking",
       "Sip warm water often|Rest and keep away from smoke and dust|Adults and children over 1 year can try warm water with a little honey|Sleep with your head slightly raised",
       "Cough lasts more than 2 weeks (please get a TB test, it is free at government centres)|You cough up blood|Breathing is hard, or there is wheezing or chest pain|High fever, night sweats or weight loss|A baby is coughing and not feeding well"),
    _s("Sore throat", "sore throat, throat pain, gala dard, throat infection, painful swallowing",
       "A cold or other virus|Dust, cold air or shouting|Allergy|Sometimes a germ called strep|Acidity",
       "Gargle with warm salt water (adults and older children)|Sip warm fluids|Rest your voice|Avoid smoke",
       "You cannot swallow, or you drool, or breathing is hard (urgent)|It lasts more than a week|High fever, white patches on the throat, or a rash|Swollen glands in the neck that keep growing"),
    _s("Cold and runny nose", "cold, runny nose, blocked nose, sneezing, zukam, sneeze, stuffy nose",
       "A common cold virus, which spreads through coughs, sneezes and touch|Allergy to dust, smoke or pollen|Change of weather",
       "Rest and drink warm fluids|Wash hands often and cover coughs and sneezes|Use your own towel and handkerchief|Sleep with your head slightly raised",
       "It lasts more than 10 days|High fever or bad pain around the nose and eyes|Wheezing or hard breathing|A baby cannot feed because of a blocked nose"),
    _s("Acidity and gas", "acidity, gas, gastric, heartburn, bloating, burning chest, indigestion, acid reflux, pet mein gas",
       "Eating very fast, or very oily and spicy meals|Long gaps between meals|Lying down right after eating|Tea or coffee on an empty stomach|Stress|Smoking",
       "Eat small meals and chew slowly|Wait 2 to 3 hours after dinner before lying down|Cut down on very oily and spicy food|Sleep with your head slightly raised|Walk a little after meals",
       "Chest pain or pressure, sweating, or pain going to the arm or jaw (could be the heart, call 108 or 112)|Black stools or vomiting blood|Trouble swallowing or weight loss|Symptoms last more than 2 weeks"),
    _s("Loose motions (diarrhoea)", "loose motion, diarrhoea, dast, loose stool, watery stool, running stomach",
       "Unsafe food or water|A tummy infection from a virus or bacteria|A food that does not suit you|Some medicines|Stress",
       "Sip ORS or fluids after every loose stool|Keep eating light food like rice, banana and dal|Wash hands with soap|Drink only boiled or safe water|Children should keep feeding, and may need zinc as the doctor says",
       "Blood or black colour in the stool|Signs of drying out: very dry mouth, little or no urine, dizziness, sunken eyes|It lasts more than 2 days|High fever or strong tummy pain|The patient is a baby, a young child or an older person (go sooner)"),
    _s("Vomiting and nausea", "vomit, vomiting, nausea, ulti, motion sickness, feel sick",
       "A stomach infection or food poisoning|Motion sickness|Migraine|Strong smells|Early pregnancy|Some medicines",
       "Take tiny sips of water or ORS|Rest, and avoid oily food|Start with light food when you feel better|Fresh air can help with motion sickness",
       "You cannot keep any fluid down for a day|There is blood in the vomit|Strong tummy pain, or pain after a head injury|Signs of drying out: very dry mouth, little urine, dizziness|The patient is a baby"),
    _s("Stomach pain", "stomach ache, stomach pain, tummy pain, abdominal pain, pet dard, belly pain",
       "Gas or indigestion|Constipation|A tummy infection|Period cramps|A food that does not suit you",
       "Rest and sip warm water|Eat light food|A warm (not hot) water bag on the tummy may soothe|Avoid oily and spicy food",
       "The pain is sudden and very strong, or the tummy is hard|Pain stays in the lower right side, with fever|You keep vomiting, or there is blood in the stool|Pain lasts more than a day|The patient is a child, or a pregnant woman"),
    _s("Back pain", "back pain, backache, kamar dard, lower back, back ache",
       "Sitting for a long time or bad posture|Lifting heavy things the wrong way|Weak muscles|An old mattress|Stress and tiredness",
       "Keep moving gently, short walks help|Do not sit for too long|Try gentle stretches|A warm cloth on the sore area may soothe|Sleep on a firm, comfortable bed",
       "Pain after a fall or accident|Numbness or weakness in the legs|Trouble passing urine or stool|Fever with back pain|Pain that wakes you at night, or lasts more than 4 weeks"),
    _s("Dizziness", "dizzy, dizziness, giddy, chakkar, lightheaded, light headed, spinning",
       "Standing up too fast|Not enough water or food|Low blood sugar or low blood pressure|Heat|Anaemia (low blood)|Poor sleep|Ear balance problems",
       "Sit or lie down right away|Sip water and eat something|Stand up slowly next time|Rest in a cool place",
       "You faint, or have chest pain or trouble breathing|Face drooping, weak arm, or slurred speech (could be a stroke, call 108 or 112 at once)|A very bad headache with dizziness|It keeps coming back|You have diabetes or blood pressure problems and feel dizzy"),
    _s("Feeling very tired", "tired, tiredness, fatigue, weakness, kamzori, low energy, no energy, weak",
       "Poor or too little sleep|Stress|Skipping meals|Anaemia (low iron)|Low vitamin D or B12|Thyroid problems|Recovering from an illness",
       "Sleep and wake at regular times|Eat regular meals with dal, vegetables, fruit, and eggs or milk|Drink enough water|Walk daily in the sunlight|Talk to someone you trust if you feel low",
       "It lasts more than 2 weeks|You are losing weight without trying, or feel breathless|You look very pale, or periods are very heavy|You feel hopeless or sad for many days|You faint"),
    _s("Mouth ulcer", "mouth ulcer, chhale, ulcer in mouth, mouth sore, mouth blister",
       "Biting your cheek by accident|Very hot or spicy food|Lack of some vitamins|Stress|Rough braces or teeth|Tummy upset",
       "Rinse with warm salt water|Avoid very hot and spicy food|Brush gently with a soft brush|Eat soft food",
       "The ulcer lasts more than 3 weeks (important, especially if you chew tobacco)|A white or red patch that does not go away|Many ulcers, or fever|You cannot eat or drink because of pain"),
    _s("Burning while passing urine", "burning urine, burning urination, burning while peeing, pain while urinating, uti, urine infection, burning pee",
       "Most often a urine infection (UTI)|Not drinking enough water in hot weather|Sometimes other infections",
       "Drink plenty of water|Do not hold urine for long|Keep the private area clean and dry|Please do not wait too long. A urine infection usually needs a doctor's test and medicine",
       "See a doctor in a day or two, even if it is mild|Go sooner if you have fever, back pain, vomiting or blood in the urine|Go sooner if you are pregnant, or if this is a child or an older person"),
]

# ------------------------------------------------- safety words (urgent cases)
CRISIS = ["suicide", "kill myself", "want to die", "end my life", "end it all", "self harm", "hurt myself"]
EMERGENCY = ["chest pain", "can t breathe", "cannot breathe", "hard to breathe", "trouble breathing",
             "not breathing", "unconscious", "heavy bleeding", "snake", "poison",
             "seizure", "stroke", "face drooping", "slurred speech", "heart attack"]

# --------------------------------------------------------------- matching
SYN = {"haldi": "turmeric", "beedi": "bidi", "gutkha": "gutka", "diarrhea": "diarrhoea",
       "vaccination": "vaccine", "vaccinated": "vaccine", "immunization": "vaccine",
       "immunisation": "vaccine", "corona": "covid", "coronavirus": "covid", "covid19": "covid",
       "babies": "baby", "newborn": "baby", "ecig": "vape", "tumor": "cancer", "cigarettes": "cigarette"}
STOP = set("a an the is are was be to of in on at and or can you your it its will if do does did that this "
           "these those for with by from my me i we they he she them have has had get gets so not no only "
           "just always never must should would could than then there their into out up about because "
           "very more most any all every one two".split())


def _norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())).strip()


def _stem(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _words(text):
    return [_stem(SYN.get(w, w)) for w in _norm(text).split()]


def _has(q, qset, kw):
    if len(kw) == 1:
        return kw[0] in qset
    n = len(kw)
    return any(q[i:i + n] == list(kw) for i in range(len(q) - n + 1))


def _prepare(items):
    for it in items:
        it["kwp"] = [tuple(_words(k)) for k in it["kw"]]
    return items


_prepare(MYTHS)
_prepare(SYMPTOMS)
for _it in MYTHS:
    _it["cw"] = {w for w in _words(_it["claim"]) if w not in STOP}
    _it["cn"] = " ".join(_words(_it["claim"]))


def _hits(item, q, qset):
    return sum(1.5 if len(k) > 1 else 1.0 for k in item["kwp"] if _has(q, qset, k))


def rank_myths(query):
    """Return [(score, keyword_hits, myth), ...] best first."""
    q = _words(query)
    qset, qn = set(q), " ".join(q)
    out = []
    for m in MYTHS:
        hits = _hits(m, q, qset)
        overlap = len(m["cw"] & qset) / max(len(m["cw"]), 1)
        ratio = SequenceMatcher(None, qn, m["cn"]).ratio()
        out.append((hits + 2.5 * overlap + 1.5 * ratio, hits, m))
    return sorted(out, key=lambda t: -t[0])


def rank_symptoms(query):
    q = _words(query)
    qset = set(q)
    found = [(_hits(s, q, qset), s) for s in SYMPTOMS]
    found = sorted([f for f in found if f[0] > 0], key=lambda t: -t[0])
    return found[:2]


MATCH, SUGGEST, URGENT_BELOW = 3.0, 1.6, 5.2


def analyze(query):
    """Main entry point. Returns a dict that the app turns into a result card."""
    q = (query or "").strip()
    if not q:
        return {"kind": "empty"}
    padded = " " + _norm(q) + " "
    if any(" " + _norm(p) + " " in padded for p in CRISIS):
        return {"kind": "crisis"}
    emergency = any(" " + _norm(p) + " " in padded for p in EMERGENCY)

    ranked = rank_myths(q)
    score, hits, best = ranked[0]
    sym = rank_symptoms(q)

    if emergency and score < URGENT_BELOW:
        return {"kind": "urgent"}  # sounds serious and is not a clear myth question
    if score >= MATCH and hits >= (sym[0][0] if sym else 0):
        related = [m for s, h, m in ranked[1:4] if s >= 2.2 and h >= 1 and m["verdict"] != "UNVERIFIED"][:2]
        return {"kind": "myth", "emergency": emergency, "item": best, "related": related}
    if sym:
        return {"kind": "symptom", "emergency": emergency, "items": [s for _, s in sym]}
    close = [m for s, h, m in ranked[:3] if s >= SUGGEST and h >= 1]
    return {"kind": "unverified", "emergency": emergency, "suggestions": close}


# ------------------------------------------------------------- quick test
if __name__ == "__main__":
    print(f"{len(MYTHS)} myths, {len(SYMPTOMS)} symptoms loaded\n")
    tests = [
        "turmeric milk cures cancer", "haldi doodh cancer cure karta hai", "I have itching on my arm",
        "garlic", "Vaccines cause autism!", "my head hurts", "eating curd at night gives cold",
        "can I take antibiotics for flu", "chest pain only gas?", "bidi is safer than cigarette",
        "my baby has fever", "tulsi kadha cures everything", "I want to die", "mosquito net malaria",
        "what is the capital of France", "sugar", "loose motion in child",
    ]
    for t in tests:
        r = analyze(t)
        if r["kind"] == "myth":
            print(f"{t!r:48} -> MYTH   {r['item']['verdict']:11} {r['item']['claim'][:46]}")
        elif r["kind"] == "symptom":
            print(f"{t!r:48} -> SYMPTOM {[s['name'] for s in r['items']]}")
        elif r["kind"] == "unverified":
            print(f"{t!r:48} -> UNVERIFIED suggestions={[m['claim'][:28] for m in r['suggestions']]}")
        else:
            print(f"{t!r:48} -> {r['kind']}")
