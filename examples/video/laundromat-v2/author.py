"""Editable episode source. Rebuild JSON manifests and the human-readable storyboard."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STYLE = "用自然清晰的普通话讲解，像和朋友认真算账。语速中等偏利落，句间短停顿，数字清楚，不拖长句尾，不要播音腔。"
ART = [
('storefront', '街角开店', 'Wide establishing view of a small Chinese neighborhood laundromat, open glass door, three front-loading machines visible inside, corgi owner carrying a laundry basket through the doorway. Sparse street outline, no written signs.'),
('payment', '手机付款', 'Close-up of a pale corgi paw holding a phone toward a small payment terminal attached to a front-loading washer. Phone screen has only a simple orange circle, no QR code, no text. Focus on the payment action, partial washer door visible.'),
('bedding', '抱被子进店', 'The corgi carrying a bulky folded duvet bigger than its torso through a laundry doorway. Two washers in the background. Medium view, practical purposeful expression, everyday customer action.'),
('campus', '校园与社区', 'A modest university dormitory laundry room with two simple commercial front-loading washers, a bench and a backpack hanging from a hook. No person, no text, no school logo. Spacious environment shot.'),
('machines', '设备配置', 'A neat bank of exactly six front-loading washers in a row, with four dryers in a separate two-by-two stack to the right. Simple white machines with orange drum accents. No people, no numbers, no labels. Wide front view.'),
('clock', '产能与需求', 'The corgi looking at a large simple wall clock above three empty washing machines. Clock has hands but no numerals. Paw raised in a questioning gesture. Medium-wide, all machines idle.'),
('delivery', '设备进场', 'The corgi carefully guiding one newly delivered commercial washing machine on a hand trolley, a simple opened cardboard crate beside it. Medium-wide, weight and effort conveyed with bent knees, no speed streaks.'),
('plumbing', '水电改造', 'An unfinished small laundry interior: exposed water pipes, floor drain, electrical box and a ventilation duct. The corgi kneeling with a measuring tape beside the washer connection. No wiring diagrams, no written labels.'),
('keys', '押金与缓冲', 'Close-up tabletop still life: a key ring, a neatly folded blank lease, a plain closed envelope and an empty laundry basket behind. One corgi paw rests beside the keys. Sparse meaningful objects, no numbers or text.'),
('loading', '投入一筒衣服', 'The corgi crouching and placing an orange towel into the open round door of a front-loading washer, one paw supports the towel, other steadies basket. Close-medium side view, action anatomically clear.'),
('transfer', '洗完再烘', 'The corgi transferring wet laundry from an open washer on the left to an open dryer on the right, holding a small basket in the middle. Two distinct machines, simple orange towel, full torso visible.'),
('detergent', '洗涤耗材', 'Close-up of a dosing pump and a plain detergent bottle connected to a washer inlet, with a few water droplets and a small orange measuring cup. No character, no labels, no arrows, no chemical formula.'),
('water', '水表计量', 'Close-up of a simple water meter connected to a clean pipe leading to a washing machine edge. Dial has a needle but no digits. A single blue water drop next to pipe, restrained orange washer accent. No person.'),
('dryer', '烘干耗能', 'Side cutaway schematic illustration of a tumble dryer: orange towel tumbling inside circular drum, a heating element below and a ventilation duct behind, simple sparse heat curves. No character, no written labels, no technical claims.'),
('receipt', '单次贡献', 'The corgi at a small laundry counter dividing a small group of coins between two shallow trays, a blank receipt curling from the payment terminal. Thoughtful expression, no calculator, no labels or numbers.'),
('calendar', '全年账本', 'Top-down view of a large blank desk calendar with regular empty squares, a laundry basket at one corner and a simple pen held by a corgi paw. No text, no digits, no real dates.'),
('lease', '固定房租', 'The corgi at a small table reading a long blank lease, holding a key ring in the other paw, two idle washing machines behind. Serious but calm expression. Medium view, no written markings.'),
('cleaning', '店主劳动', 'The corgi cleaning a dryer lint filter with a small brush beside an open dryer. Close-medium view, filter and paw action clear, a few lint tufts, no extra tools or text.'),
('repair', '维修售后', 'The corgi kneeling beside a stopped washer, checking its open lower service panel with a small wrench. A phone rests on a stool nearby. Orange towel visible in another washer. No sparks, no unsafe exposed live wiring.'),
('wear', '设备折旧', 'Close-up comparison of two otherwise identical front-loading washers: left clean and new, right with a few restrained scuffs and a loose handle, still intact. One small orange accent per washer, no labels, no dividing title.'),
('ledger', '年终算账', 'The corgi seated at a simple desk with a blank open ledger, carefully making notes with a pen; one washer behind and a small coin tray to the side. Calm accountant posture. No visible writing or calculator.'),
('quiet', '平日空机', 'Wide view of a quiet laundromat, three empty washers and two empty laundry baskets. The corgi sits on a bench looking toward the door, paws on knees, restrained concern. No clock or coins.'),
('empty', '淡季门店', 'Exterior of the same simple neighborhood laundromat at a quiet hour, open glass door, empty machines visible and a single fallen leaf on pavement. The corgi leans lightly on the doorframe. Pure white background, no signs or lettering.'),
('balance', '盈亏平衡', 'Conceptual tabletop balance scale held steady by the corgi: a small laundry basket in one pan and a stack of blank bills in the other, pans level. Single clear metaphor, no coins raining, no text or numbers.'),
('discount', '降价换客流', 'The corgi holding a plain orange price tag with no writing while looking at the payment terminal beside a washer. A small pair of scissors on counter, no cut skin, no money. Medium view, thoughtful expression.'),
('sunny', '烘干使用变化', 'The corgi hanging a freshly washed orange towel on a small outdoor drying rack, a simple sun disk above and a laundry basket below. Sparse clean line scene, no text, no clouds.'),
('rainy', '季节变化', 'The corgi entering the laundromat carrying a folded wet umbrella and laundry basket, a few rain strokes outside the doorway and dryers visible inside. No puddle hazards, no words.'),
('queue', '高峰排队', 'Three distinct corgi customers waiting with laundry baskets beside occupied machines. Main corgi wears white shirt and red collar; background customers simplified in pale gray. Short visible queue, no crowd, no written signs.'),
('location', '商圈与动线', 'Simple bird’s-eye neighborhood scene: apartment building, a small laundromat with washers visible, walking path between them. Main corgi walking along the path carrying a basket. Clearly illustrative map, not a real city map, no text or route arrows.'),
('phone', '充值与退款', 'Close-up of corgi paws holding a phone with a simple wallet icon on its otherwise blank screen, next to a payment terminal and a folded blank receipt. No numbers, no QR, no brands. Calm financial transaction scene.'),
]

# Each paragraph is synthesized naturally; its captions and shots have independent boundaries.
B = []
def block(chapter, text, art, heading, metric='', detail='', rows=None, second=None, source=None):
    shots=[{'image':f'images/{art}.png','layout':'split' if metric else 'scene','heading':heading,'metric':metric,'detail':detail}]
    if second:
        shots.append(second)
    if source:
        for s in shots:s['source']=source
    B.append({'id':f'L{len(B)+1:02d}','chapter':chapter,'text':text,'shots':shots})

def data(heading, rows, note='金额均为演示假设 · 人民币'):
    return {'layout':'table','heading':heading,'rows':[{'label':k,'value':v} for k,v in rows],'note':note}

block('01 / 先把问题问清楚','机器自己转，手机自己收钱。一家自助洗烘店，一年到底能赚多少？我们先给一个有条件的答案：这家假设门店，每天洗五十筒，税前一年剩五万七千六。','storefront','一家洗烘店，一年赚多少？',second=data('先看结果，再拆条件',[('每天洗衣','50 筒'),('年度税前利润','57,600 元')]))
block('01 / 先把问题问清楚','注意，这是社区门店的情景测算，不是真实店铺财报，也不是全国平均。所有经营数字都会标明假设。我们借上海的公开资料，解释哪些东西能查证，哪些东西必须自己核实。','ledger','先说明这本账的边界','情景测算','社区型门店 · 非行业均值')
block('01 / 先把问题问清楚','先想顾客为什么进门。可能是被子太大，也可能是家里不方便烘干。你要观察的，是附近到底有多少重复发生的洗烘需求。街上人多，只是线索，还不是订单。','bedding','谁会反复走进这家店？',second={'layout':'scene','image':'images/location.png','heading':'人流，还要变成付费需求'})
block('01 / 先把问题问清楚','公开价格也不能随便搬。上海大学二零二五年的招租公告，要求标准洗不超过四元，而且有程序时长要求。那是校园项目的价格约束，不能直接当作社区店的成交价。','campus','真实资料：校园有明确价格约束','≤ 4 元','标准洗 ≥ 40 分钟；仅此招租项目',source='上海大学招租公告 · 2025-06-20 · zcb.shu.edu.cn')
block('02 / 钱先花在哪里','现在把案例搭起来。假设六台洗衣机、四台烘干机，一年营业三百六十天。后面说的五十筒，指全店每天的洗衣循环，不是五十位顾客，也不包含烘干次数。','machines','这家假设门店长什么样？','6 洗 + 4 烘','全年营业 360 天',second=data('先统一计数单位',[('洗衣量','全店每天的洗衣循环'),('烘干量','单独计数'),('顾客数','不等于机器循环数')]))
block('02 / 钱先花在哪里','六台机器够不够，不是把一天二十四小时全排满就算完。程序耗时、顾客取衣、清洁和故障都会占时间。更关键的是，机器有空位，不代表有人愿意付款。','clock','机器产能，不等于实际需求',second={'layout':'scene','image':'images/quiet.png','heading':'空出来的时间，未必卖得掉'})
block('02 / 钱先花在哪里','先假设设备投入十八万元。这个数字只是预算位，不是厂商报价。正式选设备，要把容量、烘干方式、安装和售后写进同一张询价表，才知道报价是否能比较。','delivery','启动投入：设备','180,000 元','预算假设；需要具体型号报价')
block('02 / 钱先花在哪里','再假设改造六万元，包括给排水、电力、排风和店面施工。便宜的铺子，如果配套改造很贵，未必便宜。我们把设备和改造分开记，后面折旧也分别计算。','plumbing','启动投入：改造','60,000 元','预算假设；设备与改造分别记账',second=data('开业前的两笔投入',[('设备','180,000 元'),('改造','60,000 元'),('合计','240,000 元')]))
block('02 / 钱先花在哪里','还没结束。再留一万八押金、四万二周转金，初始现金准备一共三十万。押金不是当年费用，周转金也不能又全算一次成本。这笔钱是为了让店撑过开业爬坡。','keys','启动现金，不只设备款',second=data('初始现金准备',[('设备 + 改造','240,000'),('押金','18,000'),('周转金','42,000'),('合计','300,000')]))
block('03 / 跟着一筒衣服算','现在跟着一筒衣服走。为了看懂机制，假设洗一次成交价十二元，烘一次十元。这里用实际成交口径，不是划线原价。不同容量和不同程序，真实经营时还要继续拆。','loading','一筒衣服，先从收入算起','12 元 / 洗','烘干另计：10 元 / 次',second={'layout':'scene','image':'images/payment.png','heading':'算成交价，不算宣传原价'})
block('03 / 跟着一筒衣服算','不是每筒洗完都烘。我们假设每十筒洗衣，平均带来六次烘干。于是每筒洗衣对应的组合收入，是十二元加六元，一共十八元。后面的账，都用这个组合。','transfer','洗衣与烘干，分开计数','60%','烘干次数 ÷ 洗衣次数',second=data('组合收入',[('洗衣','12 元'),('平均附带烘干','10 × 0.6 = 6 元'),('合计','18 元 / 洗衣循环')]))
block('03 / 跟着一筒衣服算','再扣随使用发生的成本。假设每次洗衣三元，每次烘干三元，包含对应的能源、耗材和交易费用。按六成烘干比例，一筒洗衣对应四块八变动成本。','detergent','变动成本也要分别算','4.80 元','3 + 3 × 0.6',second={'layout':'scene','image':'images/dryer.png','heading':'烘干的能源成本，单独计算'})
block('03 / 跟着一筒衣服算','这些成本怎么查？比如浦东二零二三年的区属供水通知，列出了非居民综合水价。但费率只是起点。还要看门店归哪个供水区域，以及这台机器每个程序实际用了多少水。','water','真实费率，还要匹配实际用量','费率 × 用量','供水区域、计费类别、程序都要匹配',source='浦东区属非居民水价通知 · 2023-11 · pudong.gov.cn')
block('03 / 跟着一筒衣服算','设备铭牌上的千瓦是功率，账单上的度数是耗电量，两者不能直接替换。烘干还可能使用燃气。没有匹配机型和程序的实测值，三元成本就只能保留为假设。','dryer','别把功率，当成一筒的耗电','kW ≠ kWh','按机型、程序与实测账单核对')
block('03 / 跟着一筒衣服算','十八元收入减去四块八，剩十三块二。这个数字叫贡献毛利，它还要替你支付房租、人工和设备损耗。看到七成多的比例，先别急着把它叫成净利润。','receipt','这一筒，先贡献多少？','13.20 元','18 − 4.8；尚未扣固定开支',second=data('一筒的收入去向',[('组合收入','18.00'),('变动成本','−4.80'),('贡献毛利','13.20')]))
block('04 / 摊开一年账本','假设每天洗五十筒，一年就是一万八千筒，带来一万零八百次烘干。全年收入三十二万四，减去八万六千四的变动成本，留下二十三万七千六。','calendar','把单次贡献，放到全年',second=data('年度收入与贡献',[('洗衣收入','216,000'),('烘干收入','108,000'),('总收入','324,000'),('变动成本','−86,400'),('贡献毛利','237,600')]))
block('04 / 摊开一年账本','接着是房租。假设每月六千，一年七万二。这个数字不是上海租金均值，只是这本账的条件。机器今天闲着，房东也不会因此少收一天租金。','lease','固定开支：房租','72,000 元 / 年','每月 6,000 元 · 假设')
block('04 / 摊开一年账本','人工也不能写零。假设店主劳动和外包清洁合计每月四千，一年四万八。清过滤网、处理退款、接故障电话，都要有人做。这里已经计入店主劳动，后面不再扣第二遍。','cleaning','自助，不等于没有劳动','48,000 元 / 年','含店主劳动价值和外包清洁 · 假设',second={'layout':'scene','image':'images/repair.png','heading':'售后电话，也属于经营时间'})
block('04 / 摊开一年账本','维修、软件和其他运营开支，再留一年一万八的预算。实际发生可能不同，要用账单更新。上海城建职业学院的公开招租要求里，也明确写到清洁、运维和售后责任。','repair','持续经营，还有这些开支','18,000 元 / 年','维修、软件及其他运营预算 · 假设',source='劳动责任对照：上海城建职业学院公告 · 2024-12-05 · succ.edu.cn')
block('04 / 摊开一年账本','最后算折旧。假设十八万设备用六年，六万改造用五年，都不留残值，平均每年折旧四万二。这是本片的经济测算方法，不是替你确定税务折旧规则。','wear','设备损耗，要进入年账',second=data('年度折旧假设',[('设备：180,000 ÷ 6','30,000'),('改造：60,000 ÷ 5','12,000'),('年度合计','42,000')]))
block('04 / 摊开一年账本','把账合起来：二十三万七千六的贡献，减房租七万二、人工四万八、其他开支一万八、折旧四万二，税前剩五万七千六。案例不设贷款，也还没扣所得税。','ledger','现在，才轮到税前利润',second=data('基准年账',[('贡献毛利','237,600'),('房租','−72,000'),('人工','−48,000'),('其他运营','−18,000'),('折旧','−42,000'),('税前利润','57,600')]))
block('05 / 最容易变的，是客流','听起来还可以。但如果平均每天只有四十筒呢？单次贡献和固定开支不变，年度税前利润就降到一万零八十。每天少十筒，一年少赚四万七千五百二十。','quiet','每天少 10 筒，会怎样？','10,080 元','40 筒 / 日时的年度税前利润',second=data('只改变洗衣量',[('50 筒 / 日','57,600 元'),('40 筒 / 日','10,080 元'),('利润减少','47,520 元')]))
block('05 / 最容易变的，是客流','如果再降到每天三十筒，结果是全年亏三万七千四百四十。水电耗材会随订单减少，我们已经一起调低了。问题是房租、劳动预算和折旧，没跟着一起消失。','empty','每天 30 筒，进入亏损','−37,440 元','年度税前结果 · 其他条件不变')
block('05 / 最容易变的，是客流','所以先问打平要多少。全年固定开支加折旧十八万，除以每筒十三块二，再除营业天数，得到每天约三十八筒。这个门槛只在价格和烘干比例不变时成立。','balance','比年赚多少，更先要知道的数','约 38 筒 / 日','含折旧的盈亏平衡点',second=data('打平的计算',[('年度固定开支 + 折旧','180,000 元'),('单次组合贡献','13.20 元'),('营业天数','360 天'),('理论门槛','37.88 筒 / 日')]))
block('05 / 最容易变的，是客流','再看降价。洗衣每筒便宜两元，如果订单还是每天五十筒，一年就少收三万六，利润只剩两万一千六。促销是否值得，要看新增贡献能不能补上让出去的收入。','discount','便宜两元，要多卖多少？','21,600 元','洗衣降价 2 元、客流不变时的年利润')
block('05 / 最容易变的，是客流','烘干比例也会改变结果。如果每十筒只带来四次烘干，洗衣仍是每天五十筒，年利润降到三万二千四。所以不能只盯洗衣订单，还要看顾客到底买了什么。','sunny','烘干用得少，账也会变','32,400 元','烘干比例由 60% 降至 40%',second={'layout':'scene','image':'images/transfer.png','heading':'收入组合，比单一订单数更完整'})
block('05 / 最容易变的，是客流','还要把季节放进去。假设半年每天五十筒，另外半年只有三十筒，平均就是四十筒，年利润还是一万零八十。不能拿一个下雨的周末，代表全年三百六十天。','rainy','旺季一周，不能乘成全年',second=data('两个季节，同一本账',[('180 天 × 50 筒','9,000 筒'),('180 天 × 30 筒','5,400 筒'),('年均每日洗衣','40 筒'),('年度税前利润','10,080 元')]))
block('06 / 哪些经营细节会改变账','看到高峰排队，也别立刻添机器。先看排队持续多久，顾客是否真的流失，闲时又空多少。扩容会多一笔投入，只有新增订单带来的贡献，才能替这笔投入买单。','queue','排队以后，先看全年利用率',second={'layout':'scene','image':'images/machines.png','heading':'增加设备，也增加资本占用'})
block('06 / 哪些经营细节会改变账','选址要看顾客提着衣服怎么来，附近已有谁在提供同样服务，以及房子的配套是否适合。人流相似的两条街，实际订单可能不同。房租和客流必须成对比较。','location','选址，算的是需求与成本的组合',second={'layout':'scene','image':'images/lease.png','heading':'低房租与真实客流，一起看'})
block('06 / 哪些经营细节会改变账','故障损失也不只有维修单。机器停着，原本会来的订单可能去了别处。日常维护和服务响应做不好，纸上稳定的五十筒，也可能慢慢往四十筒掉。','repair','故障的成本，还包括丢掉的订单',second={'layout':'scene','image':'images/quiet.png','heading':'稳定客流，需要日常维护'})
block('06 / 哪些经营细节会改变账','再看充值。顾客今天充了钱，不代表你今天已经完成了全部服务。未来洗衣的成本还在，退款也可能发生。不能把储值到账直接当成当期利润，再全部取走。','phone','充值到账，先记清服务义务','到账 ≠ 利润','储值、消费与退款分别记录')
block('07 / 利润、现金与回本','利润和现金也要分清。基准税前利润五万七千六，加回四万二折旧，是九万九千六。这只是简化的经营现金近似，还没扣所得税、设备更新和其他资金占用变化。','ledger','利润与现金，要分别看',second=data('简化现金桥接',[('税前利润','57,600'),('加回非现金折旧','42,000'),('简化经营现金近似','99,600')],'未扣所得税、更新投入与营运资金变化；无贷款'))
block('07 / 利润、现金与回本','拿三十万初始现金除以这个近似值，静态看约三年。但这不是回本承诺。如果每天只有四十筒，同样简化算法已经接近六年；再遇更新支出，时间还会改变。','keys','静态回收期，只是一个条件计算',second=data('同样的投入，不同的客流',[('50 筒 / 日','约 3.0 年'),('40 筒 / 日','约 5.8 年')],'简化静态算法；未扣所得税、更新投入与资金占用变化'))
block('07 / 利润、现金与回本','真正准备开店，先拿到四样东西：分程序成交价、淡旺季订单、完整场地报价、匹配机型的成本。把它们逐项替换假设，比搜索一句洗衣店利润有多高，更接近答案。','receipt','让真实记录，逐项替换假设',second=data('把这四项带回账本',[('收入','分程序实际成交价'),('需求','淡旺季订单记录'),('场地','租赁与改造报价'),('设备','匹配机型的实际成本')],'资料核验清单；不是已经取得的案例数据'))
block('07 / 利润、现金与回本','如果想开第二家，也先验证第一家的订单和维护能否复制。两家店意味着两处租金、两套设备和更多协调。数量增加，不会自动把一个没打平的模型变赚钱。','storefront','开第二家之前，先验证第一家',second={'layout':'scene','image':'images/cleaning.png','heading':'复制门店，也要复制运营能力'})
block('07 / 利润、现金与回本','所以，一家自助洗烘店一年能赚多少？在这组假设里，五十筒赚五万七千六，三十筒亏三万七千四百四十。机器负责把衣服洗干净。你要负责的，是让真实需求撑得住整本账。','loading','回到最初那个问题',second=data('所有结果，都带着条件',[('50 筒 / 日','+57,600 元 / 年'),('40 筒 / 日','+10,080 元 / 年'),('30 筒 / 日','−37,440 元 / 年')],'情景测算 · 含店主劳动与折旧 · 税前 · 无贷款'))

SHORT=[]
def short(text, art, heading, metric='', detail='', second=None):
    SHORT.append({'id':f'S{len(SHORT)+1:02d}','chapter':'一分钟看懂这本账','text':text,'shots':[{'image':f'images/{art}.png','layout':'split' if metric else 'scene','heading':heading,'metric':metric,'detail':detail}]+([second] if second else [])})
short('一家自助洗烘店，一年赚多少？用一组社区店假设，算清楚。','storefront','一家洗烘店，一年赚多少？')
short('洗一次十二元，烘一次十元。假设每十筒洗衣，带来六次烘干。','loading','先看洗衣与烘干','12 元 + 10 元','分别收费 · 演示假设',{'layout':'scene','image':'images/transfer.png','heading':'每 10 筒洗衣，带来 6 次烘干'})
short('平均每筒洗衣，贡献十八元收入。扣掉四块八变动成本，剩十三块二。','detergent','先算一筒的贡献','13.20 元','18 元收入 − 4.8 元变动成本',{'layout':'scene','image':'images/payment.png','heading':'这还不是净利润'})
short('每天洗五十筒，一年营业三百六十天，全年贡献二十三万七千六。','calendar','把贡献放到全年','237,600 元','13.2 × 50 × 360')
short('再扣房租七万二，含店主劳动的人工四万八。','lease','房租和人工，仍要支付','72,000 + 48,000','年度开支 · 假设',{'layout':'scene','image':'images/cleaning.png','heading':'自助，也有人在维护'})
short('其他运营一万八，折旧四万二。税前利润，剩五万七千六。','repair','扣完开支，再看利润','57,600 元 / 年','含折旧 · 已计店主劳动 · 无贷款',data('基准年账',[('贡献毛利','237,600'),('房租 + 人工','−120,000'),('其他运营 + 折旧','−60,000'),('税前利润','57,600')]))
short('但每天只有三十筒，就会亏三万七千四百四十。','quiet','客流一变，结果就变','−37,440 元 / 年','每天洗衣 30 筒 · 其他条件不变')
short('同样条件下，平均每天约三十八筒，才能打平。','balance','先找到盈亏平衡点','约 38 筒 / 日','价格与烘干比例保持不变')
short('这些不是行业均值。真实客流、成交价和房租，才决定你最后剩多少。','receipt','用真实记录，替换这组假设','情景测算','真实经营结果，取决于门店条件')

extras={
'L02':data('两类信息，各自说明口径',[('公开资料','回到原始发布页面核查'),('经营数字','明确标为情景假设')],'社区案例；未取得实际门店财报'),
'L04':data('同叫自助洗衣，规则可能不同',[('校园项目','有专门的收费和服务条件'),('社区门店','需要实际成交价与租赁条件')],'校园项目不得直接代替社区价格样本'),
'L07':{'layout':'scene','image':'images/machines.png','heading':'先把型号、安装和售后放在一起比较'},
'L13':{'layout':'scene','image':'images/loading.png','heading':'再核实每个程序的实际耗水'},
'L14':data('两个单位，含义不同',[('kW','功率'),('kWh（度）','用电量')],'按机型与程序实测；名义功率不等于单次用电量'),
'L17':{'layout':'scene','image':'images/storefront.png','heading':'客流变化，租金仍按合同支付'},
'L19':{'layout':'scene','image':'images/phone.png','heading':'软件与售后，也需要运营预算'},
'L23':data('30 筒 / 日的年度结果',[('收入','194,400'),('变动成本','−51,840'),('固定开支 + 折旧','−180,000'),('税前利润','−37,440')]),
'L25':data('洗衣每筒降价 2 元',[('全年洗衣','18,000 筒'),('年收入减少','36,000 元'),('降价后税前利润','21,600 元')],'每天仍为 50 筒；成本和烘干比例不变'),
'L31':data('这三笔记录，分开看',[('充值','收到预付款'),('消费','履行洗烘服务'),('退款','结算未消费余额')],'不要将全部储值到账当作当期利润'),
}
for b in B:
    if b['id'] in extras:
        extra=extras[b['id']]
        if b['shots'][0].get('source'):extra['source']=b['shots'][0]['source']
        b['shots'].append(extra)

SHORT[-1]['audio_edit']={'end_seconds':8.65,'cache_fingerprint':'ec17afdae4a3819fe21e31dc','reason':'ASR 核验完整首遍于 8.3 秒结束，10.56 秒开始重复朗读；保留第一遍及短尾音。'}
B[27]['audio_edit']={'end_seconds':16.25,'cache_fingerprint':'daaec60f739e66e438705e9f','reason':'原段落读完后出现额外语音；按 ASR 测得的完整正文结束点后保留短尾音。剪辑点对应变速前音频。'}

for blocks in [SHORT,B]:
    for b in blocks:
        for shot in b['shots']:
            if shot.get('image') in [f'images/{x}.png' for x in ['receipt','machines','dryer']]:
                shot['image']=shot['image'].replace('.png','-v2.png')

COMMON={'schema_version':2,'title':'一家自助洗烘店，一年到底能赚多少？','series_label':'拥有一门生意 / 自助洗烘店','asr_hint':'简体中文。自助洗烘店，洗衣，烘干，贡献毛利，税前利润，折旧。','disclosure':'社区型门店 · 情景测算','tts':{'voice':'白桦','style':STYLE},'fps':30,'source_date':'2026-09-11'}
for label,blocks in [('short',SHORT),('long',B)]:
    (ROOT/f'{label}.json').write_text(json.dumps({**COMMON,**({'tempo':0.9469977083333333} if label=='long' else {}),'edition':label,'blocks':blocks},ensure_ascii=False,indent=2)+'\n')
    (ROOT/f'{label}-script.md').write_text('# '+COMMON['title']+'\n\n'+ '\n\n'.join(f"## {b['id']} · {b['chapter']}\n\n{b['text']}" for b in blocks)+'\n')

promptbase="Use case: illustration-story. Generate ONE standalone landscape 16:9 illustration, 1536x864 or larger, for a Chinese narrated business explainer. Reference image is ONLY character identity and line style, not its calculator, bills, text or pose. Anthropomorphic orange-and-white corgi, giant upright triangular ears, white forehead stripe and muzzle, small black eyes, red collar, white short-sleeved collared shirt, dark gray trousers, short legs and pale paws. Pure white background, fine slightly imperfect black ink contours, very restrained orange flat fills, no texture, no hatching, no gradients, no shading. Main action fills central 80 percent horizontally between y=17% and y=77%; top 14 percent and bottom 20 percent stay pure white for editable titles and subtitles. Clear large readable action, not miniature. No words, numbers, logos, QR codes or watermarks. No collage or contact sheet. New scene and different action; do not replicate the character reference pose. Scene: "
prompts=[{'id':i,'title':t,'file':f'images/{i}.png','prompt':promptbase+s} for i,t,s in ART]
(ROOT/'prompts.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2)+'\n')
lines=['# 完整镜头表','', '画面为插图；全部中文文字、数字和来源由后期叠加。分镜时间以实际配音和字幕对齐结果为准。','', '| 段落 | 核心意思/标题 | 卡型 | 配图或数据 | 标注 |','|---|---|---|---|---|']
for edition,blocks in [('短片',SHORT),('长片',B)]:
 for b in blocks:
  for s in b['shots']:
   labels=' / '.join(x for x in [s.get('metric',''),s.get('detail',''),s.get('source','')] if x)
   lines.append(f"| {edition} {b['id']} | {s['heading']} | {'数据卡' if s['layout']=='table' else '场景卡'} | {s.get('image','后期程序绘制数据表')} | {labels} |")
(ROOT/'storyboard.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':
 import re
 for name,blocks in [('short',SHORT),('long',B)]:
  print(name, 'blocks',len(blocks),'shots',sum(len(b['shots']) for b in blocks),'Han chars',len(re.findall('[\u4e00-\u9fff]',''.join(b['text'] for b in blocks))))
