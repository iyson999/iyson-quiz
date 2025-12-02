import streamlit as st
import google.generativeai as genai
import time
import json
import os
from dataclasses import dataclass
from typing import List, Dict

# --- 1. 設定與 CSS 樣式 (移植自 index.html & ResultView.tsx) ---
st.set_page_config(page_title="iyson 森老闆的廚房心理測驗", page_icon="🍳", layout="wide")

# 背景圖
BACKGROUND_IMAGE = "https://images.unsplash.com/photo-1556910103-1c02745a30bf?q=80&w=2000&auto=format&fit=crop"

# 注入 CSS
st.markdown(f"""
<style>
    /* 全站字體與背景設定 */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Noto+Sans+TC:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    }}

    /* 隱藏 Streamlit 預設元素，打造 App 質感 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* 封面與背景 */
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* 遮罩層 (讓文字在背景上更清楚) */
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.4);
        z-index: -1;
    }}

    /* 毛玻璃容器 (Glassmorphism) - 用於封面與表單 */
    .glass-container {{
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.4);
        margin-bottom: 20px;
    }}

    /* 標題樣式 */
    .title-text {{
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-weight: 800;
        color: #2D3436;
        line-height: 1.2;
        margin-bottom: 20px;
    }}
    .highlight {{ color: #E17055; }} /* Brand Orange */

    /* --- 結果報告卡片樣式 (移植自 ResultView.tsx) --- */
    .report-card {{
        background-color: #ffffff;
        border-radius: 15px;
        padding: 40px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border-left: 6px solid #E17055;
        margin-bottom: 30px;
        color: #2D3436;
    }}
    .report-title {{
        font-family: 'Playfair Display', serif;
        color: #2D3436;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }}
    .report-tag {{
        display: inline-block;
        background-color: #FCE4EC;
        color: #C2185B;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        margin-bottom: 20px;
    }}
    .report-body {{
        color: #636E72;
        font-size: 1.1rem;
        line-height: 1.8;
        text-align: justify;
    }}
    .highlight-box {{
        background-color: #F8F9FA;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        border: 1px solid #e7e5e4;
    }}
    .highlight-title {{
        color: #E17055;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }}
    
    /* 按鈕優化 */
    .stButton > button {{
        border-radius: 30px;
        padding: 10px 24px;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }}
    
    /* 讓 Streamlit 的 Radio/Select 看起來更乾淨 */
    .stRadio > div {{ background-color: transparent; }}
</style>
""", unsafe_allow_html=True)

# --- 2. 資料常數 (移植自 constants.ts) ---

QUESTIONS = [
    {
        "id": "q1",
        "question": "Q1. 【早晨儀式】週六早晨，陽光灑進廚房，這時你最理想的畫面是？",
        "options": [
            "A. 極簡靜謐：檯面空無一物，只有手沖咖啡與筆電。",
            "B. 溫馨混亂：充滿鬆餅香氣，小孩或家人在旁邊幫忙。",
            "C. 專業備戰：像個大廚，桌上擺滿食材，刀具一字排開。",
            "D. 效率出發：簡單烤個吐司，站著快速吃完準備出門。",
            "E. 綠意盎然：我在幫窗邊的香草植物澆水，像個小花園。",
            "F. 科技早晨：邊喝咖啡邊看平板新聞，或是聽著智慧音箱。",
            "G. 寵物共舞：貓咪跳上檯面，狗狗在腳邊等掉落的食物。"
        ]
    },
    {
        "id": "q2",
        "question": "Q2. 【購物戰利品】去了一趟賣場，買回來的海量戰利品怎麼辦？",
        "options": [
            "A. 展示狂人：漂亮的瓶罐當然要擺出來！放在開放層架。",
            "B. 若隱若現：放在玻璃門櫃裡，看得到又怕灰塵。",
            "C. 眼不見為淨：全部塞進櫃子深處，關上門當作沒這回事。",
            "D. 分類強迫症：每種食材都要裝進統一罐子排列整齊。",
            "E. 大量囤貨族：衛生紙買一箱、牛奶買六罐，需要倉庫般空間。",
            "F. 隨手放流派：常用調味料放爐台邊，不想開開關關。",
            "G. 酒鬼/咖啡師：食材隨便，但酒或咖啡豆一定要有專屬位置。"
        ]
    },
    {
        "id": "q3",
        "question": "Q3. 【烹飪現場】朋友突襲廚房，正在做菜的你看起來像？",
        "options": [
            "A. 優雅潔癖：備料裝小碟子，邊做邊收，隨時保持整潔。",
            "B. 戰場指揮官：鍋碗瓢盆齊飛，場面混亂但亂中有序。",
            "C. 微波大師：其實不太開火...主要是微波爐和外送盒。",
            "D. 烘焙靈魂：桌上都是麵粉、奶油、模具和攪拌機。",
            "E. 中式快炒王：大火爆炒，油煙是我的戰績。",
            "F. 科技煮夫：舒肥機、美善品、蒸烤爐...靠裝備做菜。",
            "G. 備餐狂魔：週末一次做完一週便當，需要大量空間分裝。"
        ]
    },
    {
        "id": "q4",
        "question": "Q4. 【社交距離】家裡舉辦聚餐時，身為大廚的你通常在哪裡？",
        "options": [
            "A. 舞台中央：在中島邊切水果邊聊天，我是主角。",
            "B. 幕後英雄：在封閉廚房揮汗，把完美的菜端出去。",
            "C. 團隊合作：朋友們也會擠進廚房幫忙洗菜、擺盤。",
            "D. 半開放互動：不想被看到油膩樣子，但想聽到大家聊天。",
            "E. 親子教室：廚房主要是為了教小孩做餅乾，安全第一。"
        ]
    },
    {
        "id": "q5",
        "question": "Q5. 【痛點直擊】在過去使用廚房的經驗中，哪件事最讓你「崩潰」？",
        "options": [
            "A. 撞擊障礙：轉身一直撞到把手，或是被櫃門絆倒。",
            "B. 收納黑洞：東西塞爆，拿個鍋子要移開前面那排。",
            "C. 空間窘迫：備料切菜的地方太小，切好的菜沒地方放。",
            "D. 清潔地獄：縫隙發霉、油垢卡在磁磚縫裡刷不掉。",
            "E. 身高不合：切菜要彎腰，或是洗碗會吊手，腰酸背痛。",
            "F. 蟑螂恐懼：感覺廚房死角很多，很怕小生物躲在裡面。"
        ]
    },
    {
        "id": "q6",
        "question": "Q6. 【預算價值觀】如果有額外的預算，你寧願花在哪裡？",
        "options": [
            "A. 科技解放：買一台頂級的洗碗機或蒸烤爐。",
            "B. 永恆材質：升級檯面，要那種用刀刮都不會有痕跡的石頭！",
            "C. 內在品質：花在看不見的五金，抽屜要滑順、承重要好。",
            "D. 顏值至上：門板顏色要特殊，把手要精緻，看起來高級。",
            "E. 快速完工：我不想等，誰能最快給我一套好廚具就選誰。",
            "F. 健康無毒：我家有過敏兒，甲醛含量和板材來源最重要。"
        ]
    },
    {
        "id": "q7",
        "question": "Q7. 【殘局收拾】晚餐派對結束，面對滿桌杯盤狼藉，你的習慣是？",
        "options": [
            "A. 潔癖發作：無法忍受髒亂，立刻洗起來、擦乾檯面。",
            "B. 泡水大師：碗盤丟水槽泡水，明天再說 (需要抗污材質)。",
            "C. 眼不見為淨：關燈！或是堆到看不見的角落 (需要大洗碗機)。",
            "D. 他人代勞：交給另一半或是家事人員 (需要防呆耐用設計)。"
        ]
    },
    {
        "id": "q8",
        "question": "Q8. 【家電閱兵】你的廚房裡，那些小家電 (氣炸鍋、咖啡機...) 的命運是？",
        "options": [
            "A. 閱兵大典：它們很美，全部排在檯面上展示 (需加深檯面)。",
            "B. 隱形車庫：用時再拉出來，不用時要藏起來 (需家電捲門櫃)。",
            "C. 垂直堆疊：地小人稠，希望能像大樓一樣往上蓋 (需高身電器櫃)。",
            "D. 極簡主義：我幾乎不用小家電，頂多一個快煮壺。"
        ]
    },
    {
        "id": "q9",
        "question": "Q9. 【風格直覺】最後，把你的廚房比喻成一件衣服，那會是？",
        "options": [
            "A. 黑色皮衣 (工業風/個性)",
            "B. 米白羊毛衣 (北歐風/溫暖)",
            "C. 海軍藍西裝 (輕奢風/沈穩)",
            "D. 亞麻襯衫 (鄉村風/自然)",
            "E. 清水模T恤 (侘寂風/樸實)"
        ]
    }
]

FAMILY_OPTIONS = [
    "單身貴族 (1人) - 享受獨處",
    "頂客/新婚夫妻 (2人) - 甜蜜互動",
    "新手爸媽 (有學齡前幼兒) - 安全第一",
    "成長家庭 (有國高中生) - 收納大胃王",
    "三代同堂 (長輩同住) - 友善無障礙",
    "樂齡空巢 (退休夫婦) - 質感慢生活",
    "毛孩當家 (有養貓狗) - 耐磨抗抓"
]

BUDGET_OPTIONS = [
    "10萬以下 (極簡機能/出租套房專用)", 
    "10-30萬 (經濟實惠/小資改造首選)",
    "30-60萬 (實用高CP值/標準家庭配置)",
    "60-100萬 (質感升級/進口五金配備)",
    "100-150萬 (品味生活/開放式中島規劃)",
    "150萬以上 (頂級奢華/全客製化豪宅)"
]

SIZE_OPTIONS = [
    "1坪以下 (套房迷你廚房/茶水間)",
    "1~1.5坪 (標準狹長型/一字型)",
    "1.5~2.5坪 (舒適L型/有空間放電器櫃)",
    "2.5~4坪 (夢想中島/開放式空間)",
    "4坪以上 (豪宅規格/雙廚房規劃)"
]

# --- 3. 狀態管理 (Session State) ---
if 'step' not in st.session_state:
    st.session_state.step = 'intro'
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'profile' not in st.session_state:
    st.session_state.profile = {}
if 'result_html' not in st.session_state:
    st.session_state.result_html = None
if 'result_image' not in st.session_state:
    st.session_state.result_image = None
if 'image_prompt' not in st.session_state:
    st.session_state.image_prompt = None

# --- 4. 輔助函數 ---
def reset_app():
    st.session_state.step = 'intro'
    st.session_state.responses = {}
    st.session_state.profile = {}
    st.session_state.result_html = None
    st.session_state.result_image = None
    st.session_state.image_prompt = None
    st.rerun()

# 模擬結果 (當沒有 API Key 時使用)
MOCK_HTML_RESULT = """
<div class="report-card">
    <div class="report-title">陳小姐，原來，你的廚房可以長這樣</div>
    <div class="report-tag">🔮 分析結果：溫柔的實用主義指揮官</div>
    <div class="report-body">
        根據您的測驗，我們發現您在廚房中追求的是一種「亂中有序的溫馨感」。您不介意烹飪時的熱鬧，但非常在意事後的清潔效率。
    </div>
    <br>
    <h3 style="color:#2D3436; font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">✨ 為您量身打造的三大亮點</h3>
    <div class="highlight-box">
        <div class="highlight-title">🎯 針對您的「收納焦慮」</div>
        <div class="report-body" style="font-size: 1rem;">
            由於您討厭東西塞爆，👉 <strong>推薦配置：高身拉籃 (Pantry Pull-out)</strong>，能將零食與乾貨整齊排列，一目了然。
        </div>
    </div>
    <div class="highlight-box">
        <div class="highlight-title">🍳 針對您的「清潔痛點」</div>
        <div class="report-body" style="font-size: 1rem;">
            您提到討厭縫隙發霉，👉 <strong>推薦配置：一體成型人造石水槽 + 琺瑯板壁面</strong>，油污輕輕一擦就掉。
        </div>
    </div>
    <div class="highlight-box">
        <div class="highlight-title">🎨 風格與美學建議</div>
        <div class="report-body" style="font-size: 1rem;">
             配合您喜歡的北歐風，建議採用霧面奶茶色門板搭配淺色木紋地板，營造溫暖療癒的氛圍。
        </div>
    </div>
</div>
"""

# AI 生成邏輯
def call_gemini_api(api_key, responses, profile):
    try:
        genai.configure(api_key=api_key)
        
        # 準備資料
        user_data_str = "\n".join([f"{k}: {v}" for k, v in responses.items()])
        full_profile_text = f"""
        Client Name: {profile['name']}
        Family: {profile['familyMembers']}
        Size: {profile['kitchenSize']}
        Budget: {profile['budget']}
        Quiz Answers:
        {user_data_str}
        """

        # System Prompt (移植自 geminiService.ts)
        system_prompt = f"""
        你是一位頂尖廚具設計顧問 "森老闆"。請根據測驗結果，生成一份《iyson 專屬廚房人格設計提案》。

        # 輸出規則：
        1. 不要使用 Markdown，請直接輸出 **HTML 碼**。
        2. 使用定義好的 CSS class: report-card, report-title, report-tag, highlight-box, highlight-title, report-body。
        3. 標題格式必須是："{profile['name']}，原來，你的廚房可以長這樣"
        
        # 關鍵邏輯規則：
        1. 預算 "10萬以下"：推薦美耐板/不鏽鋼，禁止推薦石英石。
        2. 預算 "60萬以上"：務必推薦石英石、BLUM五金、洗碗機。
        3. Q7 清潔習慣若選 "泡水大師"：強烈警告不可用天然石材，推薦石英石。
        4. 家庭結構：新手爸媽推 IH 爐/無把手；樂齡推洗碗機/升降櫃。

        # HTML 輸出模板：
        <div class="report-card">
            <div class="report-title">{profile['name']}，原來，你的廚房可以長這樣</div>
            <div class="report-tag">🔮 分析結果：[創意人格標籤]</div>
            <div class="report-body">[150字感性引言]</div>
            <br>
            <h3 style="color:#2D3436; font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">✨ 為您量身打造的三大亮點</h3>
            <div class="highlight-box">
                <div class="highlight-title">🎯 針對您的[痛點/習慣]</div>
                <div class="report-body" style="font-size: 1rem;">[原因] 👉 <strong>推薦配置：[產品]</strong></div>
            </div>
            <!-- 重複 2-3 個亮點 -->
            <div class="highlight-box">
                <div class="highlight-title">🎨 風格與美學建議</div>
                <div class="report-body" style="font-size: 1rem;">[風格建議]</div>
            </div>
            <div class="highlight-box">
                <div class="highlight-title">🏆 專屬系列推薦</div>
                <div class="report-body" style="font-size: 1rem;">[系列名稱與配置]</div>
            </div>
        </div>

        # 輸出 JSON 格式：
        {{ "html_content": "HTML...", "image_prompt": "English Prompt..." }}
        """

        # 1. 生成文字與 Prompt
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            contents=full_profile_text,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "html_content": {"type": "STRING"},
                        "image_prompt": {"type": "STRING"}
                    }
                }
            )
        )
        
        result_json = json.loads(response.text)
        html = result_json['html_content']
        prompt = result_json['image_prompt']

        # 2. 生成圖片 (若沒有權限或模型，這裡會失敗轉 Mock)
        # 注意：標準 Python SDK 的圖片生成語法可能與 JS SDK 不同，
        # 若使用的是支援圖片的 Model (如 gemini-pro-vision 是讀圖，imagen 是產圖)
        # 這裡為了演示穩定性，若沒有專門的 Imagen 權限，通常建議回傳 Unsplash 連結。
        # 此處保留 Prompt，圖片回傳預設圖，若您有 Imagen 權限可解開下方註解。
        
        image_url = "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?q=80&w=2070&auto=format&fit=crop"
        
        return html, image_url, prompt

    except Exception as e:
        st.error(f"AI 連線錯誤: {e}")
        return MOCK_HTML_RESULT, "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?q=80&w=2070&auto=format&fit=crop", "Mock Prompt"

# --- 5. 主程式流程 ---

# === Step 1: 封面 Intro ===
if st.session_state.step == 'intro':
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.markdown("""
        <div class="glass-container">
            <div class="title-text">
                為什麼別人做菜像拍 MV，<br>
                <span class="highlight">你卻像在打仗？</span>
            </div>
            <p style="font-size: 1.2rem; color: #636E72; line-height: 1.6;">
                <b>廚房不只是櫃子，它是你生活習慣的延伸。</b><br>
                iyson 森老闆邀請您，透過 9 道生活情境題，<br>
                找出那個懂你、順手、又療癒的「靈魂廚房」。
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("🚀 揭開我的廚房隱藏人格", use_container_width=True):
                st.session_state.step = 'quiz'
                st.rerun()
        with c2:
            st.markdown("<div style='padding-top:15px; font-weight:bold; color:#555;'>⏱️ 測驗時間：3 分鐘</div>", unsafe_allow_html=True)

# === Step 2: 測驗 Quiz ===
elif st.session_state.step == 'quiz':
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    st.title("🍳 iyson 廚房人格光譜分析")
    st.caption("請憑直覺回答，沒有對錯，只有適不適合。")
    st.divider()

    with st.form("quiz_form"):
        # 顯示題目
        for q in QUESTIONS:
            st.markdown(f"##### {q['question']}")
            sel = st.radio("選項", q['options'], key=q['id'], index=None, label_visibility="collapsed")
            if sel:
                st.session_state.responses[q['id']] = sel
            st.markdown("---")
        
        if st.form_submit_button("下一步：填寫空間需求 ✨", type="primary", use_container_width=True):
            # 檢查是否全填
            if len(st.session_state.responses) < len(QUESTIONS):
                st.warning("請回答所有問題才能準確分析喔！")
            else:
                st.session_state.step = 'form'
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# === Step 3: 表單 Form ===
elif st.session_state.step == 'form':
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    st.subheader("📐 最後一步：您的空間與預算")
    st.markdown("結合您的心理特質與實際需求，AI 將為您規劃最落地的執行方案。")
    
    with st.form("user_info"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("👤 您的稱呼", placeholder="例：陳小姐")
            family = st.selectbox("👥 家庭成員結構", FAMILY_OPTIONS)
        with col2:
            size = st.selectbox("📏 廚房大致坪數", SIZE_OPTIONS)
            budget = st.selectbox("💰 預計裝修預算 (含三機)", BUDGET_OPTIONS, help="這能協助 AI 判斷該推薦高 CP 值配置還是頂級進口方案")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # API Key 輸入 (選填，若無則使用 Mock)
        api_key = st.text_input("🔑 OpenAI/Gemini API Key (選填)", type="password", help="若未填寫將顯示範本結果")

        if st.form_submit_button("✨ 啟動 AI 智能演算", type="primary", use_container_width=True):
            if not name:
                st.warning("請輸入稱呼")
            else:
                st.session_state.profile = {
                    "name": name,
                    "familyMembers": family,
                    "kitchenSize": size,
                    "budget": budget,
                    "api_key": api_key
                }
                st.session_state.step = 'loading'
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# === Step 4: Loading & Result ===
elif st.session_state.step == 'loading':
    with st.spinner("AI 設計師正在繪製藍圖... (計算動線、材質匹配中)"):
        # 執行 AI
        api_key = st.session_state.profile.get('api_key')
        if not api_key:
            # 模擬等待
            time.sleep(2)
            html, img, prompt = MOCK_HTML_RESULT, "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?q=80&w=2070&auto=format&fit=crop", "Mock Prompt"
        else:
            html, img, prompt = call_gemini_api(api_key, st.session_state.responses, st.session_state.profile)
        
        st.session_state.result_html = html
        st.session_state.result_image = img
        st.session_state.image_prompt = prompt
        st.session_state.step = 'result'
        st.rerun()

elif st.session_state.step == 'result':
    # 兩欄佈局：左圖右文
    col_img, col_text = st.columns([1, 1.2])
    
    with col_img:
        st.image(st.session_state.result_image, use_container_width=True)
        st.caption("AI 根據您的風格生成的空間概念圖")
        with st.expander("查看 AI 繪圖指令 (Prompt)"):
            st.code(st.session_state.image_prompt)
        
        st.markdown("---")
        st.button("🔄 重新測驗", on_click=reset_app, use_container_width=True)
        st.link_button("📅 預約森老闆免費諮詢", "https://www.facebook.com/IYSON999/", use_container_width=True)

    with col_text:
        # 渲染 HTML 報告
        st.components.v1.html(st.session_state.result_html, height=800, scrolling=True)