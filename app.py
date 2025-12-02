import streamlit as st
import openai
import time

# --- 網頁基礎設定 ---
st.set_page_config(page_title="iyson 廚具心理測驗", page_icon="🍳", layout="wide")

# --- 0. 視覺樣式設定 (整合封面與報告卡片 CSS) ---
background_image_url = "https://images.unsplash.com/photo-1556910103-1c02745a30bf?q=80&w=2000&auto=format&fit=crop"

st.markdown(f"""
<style>
    /* 全站字體優化 */
    html, body, [class*="css"] {{
        font-family: "Microsoft JhengHei", "Helvetica Neue", sans-serif;
    }}
    
    /* 封面頁背景圖 */
    .cover-bg {{
        background-image: url("{background_image_url}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -1;
    }}
    
    /* 封面：毛玻璃卡片 */
    .glass-container {{
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 50px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-top: 10vh;
        max-width: 750px;
    }}
    
    /* 封面：標題文字 */
    .title-text {{
        font-size: 3.5rem;
        font-weight: 800;
        color: #2D3436;
        line-height: 1.2;
        margin-bottom: 25px;
    }}
    .highlight {{ color: #E17055; }} 
    .subtitle-text {{
        font-size: 1.3rem;
        color: #636E72;
        line-height: 1.6;
        margin-bottom: 35px;
    }}

    /* 按鈕樣式 */
    .stButton>button {{
        border-radius: 50px;
        height: 3.5em;
        font-weight: bold;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }}
    .primary-btn button {{
        background: linear-gradient(45deg, #FF7675, #D63031) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(214, 48, 49, 0.3);
        width: 100%;
    }}
    .primary-btn button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(214, 48, 49, 0.5);
    }}

    /* --- 結果頁：報告卡片樣式 --- */
    .report-card {{
        background-color: #ffffff;
        border-radius: 15px;
        padding: 40px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        border-left: 6px solid #E17055;
        margin-bottom: 30px;
        color: #2D3436;
    }}
    .report-title {{
        color: #2D3436;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 10px;
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
        border: 1px solid #eee;
    }}
    .highlight-title {{
        color: #E17055;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 8px;
    }}
</style>
""", unsafe_allow_html=True)

# --- 1. 完整題庫 (含9題) ---
questions = [
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

# --- 2. 下拉選單選項 (優化版) ---
family_options = [
    "單身貴族 (1人) - 享受獨處",
    "頂客/新婚夫妻 (2人) - 甜蜜互動",
    "新手爸媽 (有學齡前幼兒) - 安全第一",
    "成長家庭 (有國高中生) - 收納大胃王",
    "三代同堂 (長輩同住) - 友善無障礙",
    "樂齡空巢 (退休夫婦) - 質感慢生活",
    "毛孩當家 (有養貓狗) - 耐磨抗抓"
]

budget_options = [
    "10萬以下 (極簡機能/出租套房專用)", 
    "10-30萬 (經濟實惠/小資改造首選)",
    "30-60萬 (實用高CP值/標準家庭配置)",
    "60-100萬 (質感升級/進口五金配備)",
    "100-150萬 (品味生活/開放式中島規劃)",
    "150萬以上 (頂級奢華/全客製化豪宅)"
]

size_options = [
    "1坪以下 (套房迷你廚房/茶水間)",
    "1~1.5坪 (標準狹長型/一字型)",
    "1.5~2.5坪 (舒適L型/有空間放電器櫃)",
    "2.5~4坪 (夢想中島/開放式空間)",
    "4坪以上 (豪宅規格/雙廚房規劃)"
]

# --- 3. AI 邏輯核心 (輸出 HTML 版) ---
def generate_consultation(user_input, api_key=None):
    
    user_data_str = "\n".join([f"{k}: {v}" for k, v in user_input.items()])
    
    # 這裡將邏輯規則與 HTML 模板結合
    system_prompt = f"""
    你是一位擁有 20 年經驗的頂尖廚具設計顧問 "森經理"。
    請根據客戶的測驗結果，生成一份《iyson 專屬廚房人格設計提案》。

    # 關鍵邏輯規則 (Logic Rules):
    1. **預算判斷**：
       - 若預算為 "10萬以下"：強調耐用、標準規格、美耐板。禁止推薦昂貴石材或進口五金。
       - 若預算為 "60萬以上"：務必推薦賽麗石、BLUM五金、洗碗機。
    2. **清潔習慣判斷 (Q7)**：
       - 若選 "泡水大師" 或 "他人代勞"：強烈警告不可使用天然石材，必須推薦 "賽麗石" 或 "帝通石" (抗污)。
    3. **家庭結構判斷**：
       - 若是 "新手爸媽"：強調 IH 爐 (無明火安全) 與好清潔。
       - 若是 "樂齡空巢"：強調符合人體工學的洗碗機與升降櫃。

    # 輸出任務：
    請不要輸出 Markdown，請直接輸出 HTML 碼 (無需 ```html 包裹)，並使用以下模板結構：

    <div class="report-card">
        <div class="report-title">
            [填入標題，包含客戶稱呼，例如：廖先生，遇見懂您的靈魂廚房]
        </div>
        <div class="report-tag">
            🔮 您的廚房人格：[填入創意人格形容詞]
        </div>
        <div class="report-body">
            [填入感性引言，描述新廚房的生活畫面，約 150 字]
        </div>
        <br>
        <h3 style="color:#2D3436;">✨ 為您量身打造的三大亮點</h3>
        
        <div class="highlight-box">
            <div class="highlight-title">🎯 針對您的 [某個痛點或習慣]</div>
            <div class="report-body" style="font-size: 1rem;">
                [解釋為什麼] 👉 <strong>推薦配置：[具體產品名稱]</strong>
            </div>
        </div>

        <div class="highlight-box">
            <div class="highlight-title">🍳 針對您的 [家庭結構/預算考量]</div>
            <div class="report-body" style="font-size: 1rem;">
                [解釋為什麼] 👉 <strong>推薦配置：[具體產品名稱]</strong>
            </div>
        </div>
        
        <div class="highlight-box">
            <div class="highlight-title">🎨 風格與材質建議</div>
            <div class="report-body" style="font-size: 1rem;">
                [填入風格建議與配色]
            </div>
        </div>
    </div>
    
    <!-- IMAGE_PROMPT: [在此填入給 Midjourney 用的英文 Prompt, 8k, photorealistic] -->
    """

    # 模擬模式
    if not api_key:
        time.sleep(2.5)
        return f"""
        <div class="report-card">
            <div class="report-title">{user_input.get('name', '貴賓')}，遇見懂您的靈魂廚房</div>
            <div class="report-tag">🔮 您的廚房人格：優雅的效率生活家</div>
            <div class="report-body">
                根據測驗，您不只把廚房當作烹飪場所，更視其為展示品味的核心。想像清晨陽光灑落在霧面奶茶色的櫃體上，您優雅地按下咖啡機，不用擔心雜亂的電線，因為一切都已收納在專屬的電器櫃中。這就是 iyson 為您打造的夢想場景。
            </div>
            <br>
            <h3 style="color:#2D3436;">✨ 為您量身打造的三大亮點</h3>
            <div class="highlight-box">
                <div class="highlight-title">🎯 針對您的「泡水大師」習慣</div>
                <div class="report-body" style="font-size: 1rem;">
                    我們知道您討厭立刻洗碗。因此，檯面絕對禁止天然大理石。👉 <strong>推薦配置：西班牙賽麗石 (Silestone)</strong>，醬油滴整晚也不吃色。
                </div>
            </div>
            <div class="highlight-box">
                <div class="highlight-title">🍳 針對您的「收納黑洞」痛點</div>
                <div class="report-body" style="font-size: 1rem;">
                    為了讓您不再翻箱倒櫃。👉 <strong>推薦配置：BLUM 全拉式鋁灰抽屜</strong>，深處物品一目了然。
                </div>
            </div>
            <div class="highlight-box">
                <div class="highlight-title">🎨 風格建議</div>
                <div class="report-body" style="font-size: 1rem;">
                    以北歐風為基底，搭配霧面奶茶色門板與暖色溫燈光，營造溫馨氛圍。
                </div>
            </div>
        </div>
        <!-- IMAGE_PROMPT: Photorealistic interior photography of a warm Scandinavian kitchen... -->
        """

    # 真實 AI 模式
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o", # 若無 gpt-4o 可改 gpt-3.5-turbo
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"客戶資料：\n{user_data_str}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"<div class='report-card'>AI 連線錯誤：{str(e)}</div>"

# --- 4. 頁面邏輯控制 ---

# 初始化狀態
if 'page' not in st.session_state:
    st.session_state.started = False
    st.session_state.page = 'quiz'
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# === 頁面 A: 電影感封面 ===
if not st.session_state.started:
    # 顯示背景圖層
    st.markdown('<div class="cover-bg"></div>', unsafe_allow_html=True)
    
    # 顯示內容
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.markdown(f"""
        <div class="glass-container">
            <div class="title-text">
                為什麼別人做菜像拍 MV，<br>
                <span class="highlight">你卻像在打仗？</span>
            </div>
            <div class="subtitle-text">
                <b>廚房不只是櫃子，它是你生活習慣的延伸。</b><br>
                iyson 森經理邀請您，透過 9 道生活情境題，<br>
                找出那個懂你、順手、又療癒的「靈魂廚房」。
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 按鈕區
        b1, b2 = st.columns([1, 1])
        with b1:
            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            if st.button("🚀 揭開我的廚房隱藏人格"):
                st.session_state.started = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with b2:
            st.markdown("<div style='padding-top: 15px; color: white; text-shadow: 1px 1px 4px rgba(0,0,0,0.8);'><b>⏱️ 測驗時間：3 分鐘</b></div>", unsafe_allow_html=True)

# === 頁面 B: 心理測驗表單 ===
elif st.session_state.page == 'quiz':
    st.title("🍳 iyson 廚房人格光譜分析")
    st.caption("請憑直覺回答，沒有對錯，只有適不適合。")
    st.divider()

    with st.form("quiz_form"):
        # 1. 心理測驗題
        user_responses = {}
        for q in questions:
            st.markdown(f"##### {q['question']}")
            choice = st.radio("選項", q['options'], key=q['id'], label_visibility="collapsed", index=None)
            user_responses[q['id']] = choice
            st.markdown("---")
        
        # 2. 基本資料與硬體需求
        st.markdown("#### 📐 最後一步：您的空間需求")
        
        col_a, col_b = st.columns(2)
        with col_a:
            family = st.selectbox("👥 家庭成員結構", family_options)
            k_size = st.selectbox("📏 廚房大致坪數", size_options)
        with col_b:
            budget = st.selectbox("💰 預計裝修預算 (含三機)", budget_options)
            name = st.text_input("👤 您的稱呼 (必填)", placeholder="例：廖先生")

        # 提交按鈕
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("✨ 啟動 AI 智能演算", type="primary", use_container_width=True)

        if submit_btn:
            if not name:
                st.warning("請輸入您的稱呼，讓我們為您生成專屬報告。")
            elif any(v is None for v in user_responses.values()):
                st.warning("請完成所有題目喔！")
            else:
                user_responses['name'] = name
                user_responses['family'] = family
                user_responses['budget'] = budget
                user_responses['size'] = k_size
                
                st.session_state.answers = user_responses
                st.session_state.page = 'result'
                st.rerun()

# === 頁面 C: 分析結果 ===
elif st.session_state.page == 'result':
    st.balloons()
    
    # 側邊欄輸入 Key (只在結果頁需要用到)
    with st.sidebar:
        st.header("⚙️ 關於本系統")
        st.info("AI 運算核心：OpenAI GPT-4")
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
        else:
            api_key = st.text_input("輸入 OpenAI API Key", type="password")
    
    # AI 運算
    with st.spinner('AI 設計師正在建構您的空間藍圖...'):
        full_response = generate_consultation(st.session_state.answers, api_key)
        
        # 分離 Image Prompt
        if "IMAGE_PROMPT:" in full_response:
            html_content = full_response.split("<!-- IMAGE_PROMPT:")[0]
        else:
            html_content = full_response

    # 結果呈現 (左文右圖)
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        # 重點：開啟 HTML 渲染功能
        st.markdown(html_content, unsafe_allow_html=True)
    
    with c2:
        st.markdown("### 🖼️ 未來空間想像")
        # 這裡用假圖示意，若有 DALL-E 可直接換成生成的 URL
        st.image("[https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=1000&auto=format&fit=crop](https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=1000&auto=format&fit=crop)", 
                 caption="AI Concept Art", use_container_width=True)
        
        st.success("喜歡這個提案嗎？")
        st.button("📅 預約森經理免費諮詢", type="primary", use_container_width=True)
        st.button("💬 加入官方 LINE 討論", use_container_width=True)
        
        if st.button("🔄 重新測驗"):
            st.session_state.page = 'quiz'
            st.rerun()