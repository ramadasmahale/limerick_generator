import transformers
import torch
import torch.nn.functional as F
from torch import nn
from torch.cuda.amp import custom_fwd, custom_bwd
from bitsandbytes.functional import quantize_blockwise, dequantize_blockwise
from tqdm.auto import tqdm
from phonemizer import phonemize
from phonemizer.separator import Separator
import nltk
nltk.download('punkt')
import sys
sys.path.append("GRUEN")
import GRUEN.Main as gruen
import sys
sys.path.append("/content/detoxify")
from detoxify import Detoxify


import string as str
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import torch.nn.functional as F
from random import randint, seed
import math
import pickle 
import re
import sys

sys.path.append("./wmd-relax/wmd/")


# TO DO: force last token to end a sentence
# revise previous lines if we can't find a good rhyme

punctuation = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 58, 59, 60, 61, 62, 63, 90, 91, 92, 93, 220, 352, 357, 362, 366, 405, 438, 486, 492, 513, 526, 532, 553, 580, 604, 642, 650, 657, 678, 685, 705, 718, 720, 737, 764, 767, 796, 807, 828, 830, 834, 837, 838, 855, 860, 930, 939, 940, 982, 986, 1003, 1058, 1065, 1105, 1106, 1120, 1129, 1157, 1160, 1174, 1220, 1222, 1238, 1248, 1264, 1267, 1270, 1279, 1298, 1303, 1314, 1315, 1343, 1367, 1377, 1378, 1391, 1415, 1421, 1427, 1433, 1467, 1478, 1485, 1495, 1507, 1511, 1539, 1542, 1558, 1584, 1594, 1596, 1600, 1635, 1679, 1701, 1731, 1776, 1782, 1783, 1795, 1802, 1821, 1828, 1853, 1875, 1899, 1911, 1946, 1954, 1959, 1983, 1987, 2014, 2026, 2075, 2078, 2079, 2091, 2109, 2154, 2162, 2167, 2177, 2211, 2231, 2235, 2242, 2310, 2319, 2321, 2327, 2361, 2388, 2404, 2414, 2425, 2430, 2466, 2474, 2481, 2488, 2534, 2548, 2559, 2579, 2598, 2599, 2602, 2608, 2623, 2624, 2625, 2637, 2644, 2670, 2681, 2682, 2713, 2718, 2757, 2780, 2791, 2808, 2813, 2816, 2857, 2864, 2919, 2920, 2931, 2996, 2998, 2999, 3023, 3050, 3064, 3070, 3104, 3126, 3132, 3134, 3228, 3256, 3261, 3270, 3312, 3324, 3365, 3373, 3388, 3419, 3439, 3459, 3467, 3510, 3548, 3553, 3556, 3559, 3571, 3648, 3682, 3693, 3695, 3712, 3717, 3720, 3784, 3829, 3865, 3880, 3901, 3933, 3980, 4008, 4019, 4032, 4051, 4059, 4064, 4083, 4089, 4101, 4153, 4181, 4211, 4242, 4275, 4304, 4309, 4310, 4317, 4343, 4349, 4353, 4357, 4407, 4458, 4521, 4524, 4531, 4557, 4570, 4600, 4613, 4626, 4747, 4751, 4761, 4764, 4770, 4790, 4793, 4808, 4841, 4846, 4869, 4880, 4895, 4907, 4943, 4967, 4974, 5014, 5066, 5075, 5125, 5145, 5214, 5218, 5237, 5299, 5304, 5320, 5323, 5332, 5333, 5433, 5441, 5472, 5512, 5534, 5539, 5598, 5607, 5619, 5633, 5705, 5769, 5774, 5816, 5824, 5846, 5855, 5867, 5878, 5892, 5946, 5974, 5996, 5999, 6052, 6073, 6135, 6200, 6244, 6298, 6303, 6329, 6337, 6390, 6420, 6469, 6624, 6640, 6659, 6739, 6740, 6852, 6885, 6927, 6957, 6999, 7029, 7061, 7131, 7169, 7175, 7192, 7198, 7203, 7225, 7265, 7337, 7358, 7359, 7388, 7410, 7441, 7479, 7499, 7559, 7600, 7618, 7632, 7643, 7665, 7724, 7769, 7795, 7804, 7816, 7863, 7874, 7879, 7904, 7908, 7930, 7982, 8054, 8069, 8093, 8133, 8162, 8172, 8183, 8190, 8235, 8257, 8269, 8275, 8298, 8309, 8348, 8351, 8412, 8454, 8487, 8541, 8576, 8614, 8628, 8644, 8646, 8684, 8699, 8702, 8728, 8735, 8753, 8762, 8784, 8854, 8864, 8870, 8915, 8949, 8964, 8973, 9031, 9063, 9130, 9162, 9166, 9193, 9225, 9313, 9415, 9466, 9507, 9508, 9609, 9656, 9661, 9698, 9705, 9768, 9773, 9783, 9796, 9804, 9805, 9816, 9832, 9849, 9879, 9907, 9919, 9959, 10048, 10052, 10053, 10083, 10091, 10097, 10111, 10148, 10163, 10185, 10190, 10221, 10232, 10249, 10261, 10333, 10354, 10460, 10495, 10531, 10535, 10541, 10563, 10612, 10779, 10786, 11024, 11037, 11074, 11097, 11104, 11139, 11207, 11208, 11245, 11323, 11405, 11420, 11442, 11445, 11470, 11485, 11496, 11502, 11509, 11528, 11537, 11546, 11592, 11593, 11623, 11639, 11645, 11709, 11757, 11785, 11900, 11907, 11919, 12095, 12113, 12122, 12131, 12179, 12195, 12240, 12248, 12279, 12340, 12359, 12404, 12429, 12713, 12726, 12762, 12813, 12825, 12844, 12863, 12865, 12877, 12878, 12923, 12952, 12962, 13018, 13037, 13108, 13130, 13151, 13163, 13219, 13330, 13343, 13348, 13374, 13381, 13412, 13426, 13454, 13464, 13498, 13521, 13531, 13538, 13539, 13540, 13557, 13679, 13702, 13803, 13841, 13896, 13979, 13984, 14004, 14030, 14062, 14079, 14198, 14223, 14280, 14315, 14373, 14436, 14454, 14468, 14489, 14512, 14585, 14610, 14631, 14656, 14686, 14692, 14726, 14745, 14804, 14808, 14877, 14956, 14980, 15089, 15090, 15116, 15136, 15143, 15179, 15187, 15197, 15211, 15231, 15259, 15277, 15306, 15341, 15349, 15363, 15377, 15408, 15426, 15437, 15473, 15495, 15506, 15524, 15533, 15589, 15629, 15674, 15696, 15711, 15724, 15729, 15761, 15801, 15853, 15885, 15886, 15897, 15904, 15913, 15920, 15931, 15963, 15982, 16003, 16078, 16088, 16101, 16102, 16150, 16151, 16193, 16208, 16226, 16236, 16243, 16315, 16317, 16327, 16382, 16410, 16450, 16471, 16489, 16529, 16562, 16589, 16616, 16626, 16677, 16679, 16725, 16763, 16791, 16792, 16799, 16817, 16822, 16942, 16945, 16994, 17020, 17031, 17032, 17059, 17174, 17202, 17241, 17279, 17318, 17342, 17405, 17414, 17426, 17430, 17464, 17477, 17501, 17544, 17553, 17569, 17572, 17575, 17635, 17643, 17657, 17672, 17729, 17759, 17816, 17817, 17827, 17885, 17912, 17971, 18005, 18083, 18109, 18112, 18125, 18161, 18182, 18189, 18237, 18294, 18298, 18376, 18395, 18444, 18458, 18477, 18500, 18523, 18604, 18638, 18693, 18741, 18742, 18781, 18823, 18897, 18938, 18946, 19004, 19035, 19038, 19039, 19048, 19060, 19104, 19153, 19203, 19214, 19244, 19322, 19342, 19351, 19355, 19409, 19415, 19420, 19424, 19427, 19442, 19504, 19510, 19529, 19570, 19571, 19588, 19622, 19629, 19683, 19707, 19708, 19710, 19755, 19779, 19782, 19841, 19880, 19884, 19891, 19924, 19953, 19969, 19990, 20004, 20007, 20033, 20064, 20107, 20167, 20198, 20219, 20224, 20233, 20248, 20262, 20299, 20343, 20356, 20368, 20370, 20379, 20416, 20479, 20483, 20510, 20520, 20548, 20598, 20662, 20666, 20679, 20708, 20740, 20789, 20809, 20924, 20943, 20959, 20964, 20986, 20995, 21017, 21033, 21056, 21113, 21139, 21148, 21215, 21261, 21268, 21273, 21288, 21315, 21355, 21387, 21395, 21409, 21431, 21489, 21495, 21498, 21503, 21526, 21536, 21577, 21599, 21601, 21626, 21643, 21652, 21709, 21719, 21734, 21737, 21738, 21747, 21761, 21777, 21794, 21807, 21844, 21895, 21908, 21912, 21940, 22039, 22042, 22047, 22131, 22133, 22135, 22136, 22148, 22169, 22172, 22186, 22219, 22241, 22243, 22288, 22291, 22305, 22318, 22330, 22337, 22345, 22352, 22369, 22370, 22413, 22416, 22446, 22458, 22492, 22515, 22538, 22544, 22567, 22572, 22579, 22613, 22626, 22666, 22675, 22709, 22717, 22725, 22730, 22745, 22759, 22784, 22799, 22800, 22831, 22842, 22855, 22857, 22883, 22909, 22913, 22914, 22935, 22951, 22955, 22980, 22985, 22986, 22995, 22996, 23029, 23031, 23045, 23055, 23120, 23134, 23148, 23188, 23193, 23195, 23234, 23237, 23313, 23330, 23336, 23344, 23349, 23362, 23378, 23451, 23460, 23487, 23516, 23539, 23601, 23628, 23664, 23666, 23679, 23721, 23726, 23734, 23753, 23756, 23785, 23815, 23846, 23847, 23859, 23871, 23884, 23906, 23924, 23926, 23984, 24018, 24022, 24036, 24038, 24041, 24045, 24063, 24096, 24136, 24137, 24168, 24200, 24214, 24217, 24235, 24293, 24294, 24305, 24309, 24339, 24356, 24369, 24403, 24409, 24414, 24457, 24465, 24529, 24555, 24591, 24598, 24618, 24620, 24648, 24652, 24669, 24693, 24718, 24760, 24793, 24839, 24840, 24844, 24848, 24894, 24909, 24938, 24940, 24943, 24970, 24977, 24991, 25022, 25054, 25061, 25090, 25096, 25106, 25113, 25128, 25150, 25177, 25181, 25190, 25191, 25226, 25240, 25248, 25257, 25264, 25270, 25272, 25295, 25307, 25325, 25326, 25399, 25429, 25475, 25500, 25508, 25540, 25597, 25600, 25609, 25643, 25644, 25645, 25658, 25666, 25667, 25674, 25698, 25707, 25710, 25719, 25764, 25780, 25787, 25816, 25829, 25836, 25838, 25859, 25870, 25887, 25915, 25947, 25948, 25964, 25970, 25998, 26007, 26033, 26050, 26063, 26073, 26076, 26115, 26118, 26143, 26171, 26200, 26214, 26250, 26259, 26276, 26279, 26290, 26352, 26358, 26398, 26422, 26427, 26429, 26481, 26488, 26492, 26513, 26514, 26525, 26539, 26561, 26582, 26598, 26607, 26660, 26700, 26704, 26709, 26717, 26753, 26780, 26793, 26826, 26833, 26866, 26867, 26881, 26894, 26895, 26912, 26933, 26937, 26956, 26989, 27007, 27019, 27033, 27037, 27057, 27071, 27097, 27121, 27137, 27156, 27191, 27192, 27193, 27203, 27211, 27228, 27230, 27246, 27253, 27260, 27267, 27277, 27301, 27310, 27326, 27367, 27368, 27371, 27408, 27412, 27422, 27444, 27493, 27514, 27550, 27551, 27559, 27584, 27613, 27621, 27641, 27649, 27653, 27691, 27693, 27696, 27712, 27720, 27728, 27754, 27778, 27790, 27791, 27795, 27800, 27824, 27829, 27877, 27896, 27936, 27937, 27956, 27970, 27972, 27988, 28011, 28013, 28017, 28041, 28054, 28072, 28104, 28112, 28119, 28174, 28200, 28256, 28262, 28264, 28265, 28277, 28296, 28324, 28358, 28362, 28369, 28401, 28404, 28460, 28481, 28551, 28555, 28560, 28567, 28581, 28592, 28598, 28645, 28658, 28669, 28676, 28684, 28687, 28688, 28694, 28714, 28725, 28727, 28771, 28815, 28817, 28857, 28872, 28878, 28896, 28933, 28947, 28955, 28977, 28978, 28988, 29001, 29006, 29022, 29041, 29059, 29088, 29101, 29110, 29113, 29119, 29143, 29159, 29164, 29173, 29211, 29217, 29225, 29226, 29228, 29279, 29300, 29326, 29331, 29334, 29335, 29342, 29343, 29414, 29416, 29513, 29524, 29558, 29565, 29568, 29577, 29626, 29637, 29653, 29691, 29694, 29703, 29720, 29769, 29795, 29796, 29807, 29847, 29865, 29903, 29953, 29994, 30005, 30057, 30072, 30109, 30110, 30120, 30123, 30138, 30179, 30206, 30272, 30273, 30290, 30299, 30336, 30368, 30420, 30435, 30453, 30460, 30478, 30483, 30484, 30487, 30505, 30543, 30557, 30607, 30610, 30629, 30695, 30704, 30727, 30743, 30763, 30803, 30823, 30827, 30863, 30866, 30924, 30934, 30960, 30986, 30989, 30992, 30995, 31009, 31010, 31011, 31020, 31027, 31034, 31046, 31051, 31064, 31102, 31113, 31115, 31128, 31161, 31175, 31211, 31360, 31380, 31386, 31418, 31478, 31495, 31496, 31503, 31510, 31520, 31552, 31566, 31575, 31654, 31666, 31672, 31675, 31697, 31714, 31751, 31773, 31794, 31820, 31883, 31911, 31916, 31936, 31938, 31952, 31953, 31980, 31982, 32047, 32056, 32059, 32062, 32066, 32090, 32092, 32105, 32114, 32118, 32128, 32148, 32158, 32182, 32190, 32196, 32203, 32215, 32216, 32220, 32239, 32284, 32320, 32321, 32382, 32406, 32417, 32459, 32471, 32501, 32509, 32531, 32535, 32544, 32568, 32576, 32583, 32590, 32591, 32614, 32624, 32637, 32642, 32647, 32747, 32756, 32759, 32811, 32817, 32843, 32865, 32869, 32883, 32921, 32941, 32996, 33015, 33028, 33032, 33042, 33047, 33057, 33116, 33121, 33151, 33153, 33160, 33172, 33206, 33223, 33250, 33283, 33289, 33300, 33319, 33372, 33394, 33400, 33409, 33438, 33448, 33459, 33470, 33490, 33507, 33529, 33535, 33548, 33551, 33580, 33581, 33618, 33638, 33646, 33660, 33690, 33698, 33717, 33747, 33759, 33761, 33781, 33797, 33808, 33809, 33813, 33879, 33882, 33916, 33924, 33942, 33963, 33981, 33994, 34013, 34044, 34085, 34091, 34107, 34125, 34131, 34135, 34137, 34155, 34159, 34171, 34206, 34215, 34229, 34251, 34256, 34287, 34294, 34323, 34353, 34373, 34385, 34400, 34427, 34463, 34465, 34483, 34489, 34507, 34516, 34583, 34598, 34604, 34607, 34617, 34620, 34625, 34626, 34635, 34713, 34716, 34729, 34741, 34758, 34770, 34772, 34801, 34808, 34825, 34865, 34913, 34938, 34949, 34951, 35005, 35038, 35090, 35124, 35126, 35133, 35145, 35148, 35150, 35175, 35195, 35218, 35264, 35273, 35307, 35343, 35360, 35369, 35378, 35379, 35384, 35402, 35404, 35411, 35419, 35430, 35435, 35447, 35494, 35500, 35514, 35534, 35540, 35549, 35592, 35617, 35625, 35638, 35642, 35656, 35665, 35667, 35709, 35713, 35745, 35751, 35768, 35793, 35809, 35844, 35890, 35897, 35916, 35922, 35937, 35944, 35978, 35989, 36006, 36042, 36058, 36088, 36094, 36100, 36117, 36141, 36147, 36150, 36189, 36203, 36243, 36244, 36260, 36330, 36338, 36445, 36453, 36463, 36475, 36490, 36521, 36561, 36563, 36565, 36566, 36625, 36626, 36629, 36641, 36657, 36658, 36676, 36678, 36680, 36720, 36737, 36786, 36792, 36796, 36809, 36864, 36879, 36911, 36917, 36928, 36937, 36959, 36966, 36993, 37082, 37128, 37144, 37160, 37166, 37187, 37224, 37227, 37250, 37255, 37272, 37283, 37290, 37309, 37364, 37381, 37397, 37404, 37405, 37452, 37466, 37498, 37517, 37528, 37547, 37563, 37576, 37601, 37633, 37637, 37667, 37674, 37680, 37688, 37710, 37730, 37737, 37747, 37750, 37781, 37804, 37811, 37831, 37841, 37856, 37864, 37867, 37913, 37922, 37950, 37967, 37981, 37988, 37991, 38016, 38055, 38056, 38073, 38089, 38093, 38107, 38108, 38123, 38147, 38155, 38158, 38165, 38172, 38190, 38205, 38210, 38214, 38219, 38249, 38314, 38326, 38339, 38362, 38369, 38377, 38380, 38381, 38384, 38391, 38430, 38431, 38446, 38449, 38472, 38503, 38508, 38525, 38547, 38549, 38565, 38569, 38595, 38605, 38612, 38634, 38652, 38703, 38721, 38783, 38819, 38831, 38850, 38867, 38892, 38902, 38905, 38907, 38956, 39064, 39084, 39088, 39093, 39101, 39103, 39111, 39115, 39118, 39121, 39132, 39135, 39166, 39174, 39188, 39195, 39226, 39251, 39254, 39260, 39277, 39280, 39320, 39322, 39357, 39380, 39397, 39434, 39449, 39466, 39506, 39509, 39570, 39595, 39647, 39658, 39667, 39697, 39710, 39761, 39763, 39768, 39850, 39861, 39864, 39882, 39885, 39893, 39923, 39925, 39937, 39997, 40022, 40035, 40064, 40090, 40103, 40111, 40149, 40173, 40179, 40215, 40220, 40248, 40256, 40264, 40271, 40278, 40286, 40350, 40353, 40384, 40385, 40393, 40400, 40401, 40403, 40417, 40427, 40454, 40463, 40484, 40486, 40523, 40538, 40554, 40585, 40639, 40643, 40652, 40654, 40660, 40675, 40703, 40719, 40720, 40736, 40754, 40761, 40791, 40828, 40839, 40873, 40884, 41019, 41023, 41052, 41060, 41103, 41172, 41208, 41234, 41235, 41241, 41247, 41263, 41287, 41289, 41290, 41292, 41322, 41349, 41417, 41423, 41424, 41435, 41436, 41441, 41507, 41531, 41544, 41561, 41569, 41573, 41580, 41583, 41612, 41625, 41647, 41655, 41706, 41707, 41717, 41734, 41739, 41761, 41810, 41813, 41820, 41832, 41853, 41874, 41879, 41888, 41906, 41922, 41931, 41934, 41948, 41977, 42018, 42032, 42060, 42117, 42141, 42163, 42199, 42210, 42215, 42224, 42240, 42246, 42250, 42294, 42303, 42313, 42321, 42334, 42363, 42444, 42479, 42489, 42496, 42501, 42520, 42534, 42535, 42548, 42622, 42638, 42669, 42671, 42691, 42716, 42720, 42744, 42751, 42752, 42759, 42780, 42785, 42802, 42819, 42830, 42875, 42877, 42911, 42924, 42944, 42947, 42980, 43019, 43053, 43054, 43134, 43147, 43155, 43179, 43184, 43193, 43234, 43239, 43240, 43284, 43292, 43313, 43336, 43356, 43364, 43367, 43379, 43434, 43452, 43489, 43509, 43526, 43550, 43564, 43571, 43587, 43610, 43634, 43637, 43641, 43661, 43665, 43686, 43690, 43697, 43704, 43722, 43734, 43785, 43798, 43801, 43825, 43839, 43864, 43916, 43918, 43922, 43927, 43950, 43977, 44063, 44084, 44085, 44087, 44093, 44103, 44104, 44167, 44169, 44183, 44212, 44214, 44215, 44218, 44227, 44230, 44233, 44274, 44300, 44318, 44341, 44361, 44367, 44386, 44388, 44417, 44427, 44435, 44438, 44465, 44468, 44505, 44541, 44550, 44552, 44578, 44586, 44587, 44613, 44617, 44622, 44626, 44627, 44646, 44648, 44673, 44675, 44688, 44698, 44713, 44717, 44729, 44750, 44785, 44807, 44808, 44821, 44825, 44826, 44856, 44912, 44926, 44928, 44966, 44969, 44980, 44994, 45021, 45039, 45063, 45068, 45088, 45095, 45144, 45151, 45160, 45191, 45192, 45210, 45214, 45271, 45278, 45297, 45299, 45302, 45310, 45326, 45331, 45337, 45340, 45345, 45385, 45403, 45418, 45422, 45432, 45434, 45438, 45439, 45440, 45455, 45469, 45473, 45491, 45537, 45598, 45600, 45601, 45611, 45620, 45719, 45720, 45722, 45734, 45758, 45791, 45839, 45881, 45900, 45937, 45959, 45969, 45987, 46044, 46068, 46083, 46096, 46110, 46111, 46121, 46239, 46244, 46249, 46250, 46302, 46328, 46351, 46352, 46393, 46396, 46402, 46424, 46425, 46435, 46438, 46444, 46477, 46491, 46519, 46556, 46570, 46572, 46581, 46588, 46589, 46618, 46633, 46636, 46660, 46712, 46720, 46723, 46752, 46761, 46815, 46821, 46839, 46841, 46866, 46871, 46872, 46899, 46900, 46904, 46939, 46951, 46956, 46957, 47007, 47026, 47072, 47082, 47101, 47106, 47113, 47159, 47175, 47182, 47197, 47202, 47226, 47232, 47233, 47235, 47253, 47282, 47308, 47325, 47338, 47343, 47372, 47396, 47407, 47448, 47454, 47465, 47493, 47505, 47512, 47521, 47527, 47540, 47567, 47576, 47580, 47582, 47671, 47679, 47682, 47705, 47715, 47744, 47760, 47762, 47784, 47785, 47795, 47801, 47835, 47838, 47915, 47932, 47934, 47936, 47941, 47946, 47996, 48000, 48057, 48065, 48069, 48082, 48096, 48104, 48132, 48136, 48156, 48170, 48173, 48185, 48193, 48194, 48200, 48207, 48219, 48220, 48246, 48250, 48252, 48284, 48290, 48340, 48341, 48365, 48372, 48391, 48443, 48475, 48524, 48527, 48528, 48529, 48531, 48548, 48555, 48564, 48581, 48597, 48600, 48602, 48609, 48630, 48634, 48638, 48645, 48655, 48683, 48688, 48712, 48724, 48725, 48758, 48768, 48774, 48777, 48868, 48874, 48882, 48889, 48891, 48894, 48908, 48952, 48964, 48999, 49020, 49029, 49051, 49074, 49082, 49087, 49125, 49129, 49146, 49150, 49211, 49231, 49234, 49259, 49287, 49294, 49296, 49327, 49351, 49352, 49356, 49388, 49429, 49447, 49489, 49503, 49517, 49539, 49541, 49542, 49545, 49557, 49561, 49563, 49584, 49616, 49633, 49641, 49649, 49658, 49669, 49682, 49689, 49703, 49704, 49721, 49778, 49803, 49814, 49841, 49856, 49888, 49934, 49946, 49954, 49959, 49989, 49995, 50038, 50049, 50055, 50080, 50113, 50119, 50138, 50148, 50150, 50154, 50155, 50165, 50184, 50205, 50242, 50247}
acceptable_punctuation = {13, 0, 11, 30, 25, 26, 6, 1, 7, 8, 438, 12, 705, 357,1267,366,705,1377,220,764}
end_punctuation ={0,13,11,26,30}
class Struct:
    pass
params = Struct()
params.rhyme_set_size = 20  # if a word will later be rhymed with, at least this many rhyming words must exist
params.probability_threshold = .00005 # a token must have at least this probability of being the next token. .02 = better quality but slower; .0005 = worse quality but faster. If you use one-syllable suppression, these limits should be more like .005 and .00005.
params.line_probability_threshold = 0 #total multiplied out probability of entire line of tokens can be no lower than this. 0 means this isn't being used.
params.ultimate_expansion = 1000 # no more than this many words will be tried as the last syllable for any previous phrase
params.penultimate_expansion = 10 # no more than this many words will be tried for the next to last syllable for any previous phrase
params.other_expansion = 10 # no more than this many words will be tried for the second through next to last syllables of any phrase
params.random_seed = 28 # if the seed and prompt are the same, the poem will be the same
params.line_end_punctuation_constraint = True
params.punctuation_probability_threshold = .001
params.model_name = "gpt2-xl" # change this to "gpt2-xl" to get started. "poetry" requires a lot more effort to get running-- see the README for details.
params.stuck_counter_limit = 1000
params.one_syllable_suppression = 20
debug = False

poem_line = [""] * 100000
rhyme_dictionary = []
reverse_rhyme_dictionary = []
bad_rhymes = []
syllable_count_dictionary = []
rhyming_tokens = []
syllable_tokens = []
stress_dictionary = []
stress_tokens = []
stuck_counter = 0
past_backup= []


def xprint(*args, **kwargs):
    #only prints if "debug" is turned on. It has a try block so that it never throws errors of its own.
    global debug
    if debug == True:
        print("RAMTEST")
        try:
            print(*args, **kwargs)
        except:
            print("error in printing")
                
def text_to_meter(text, stress_dictionary):
    global punctuation
    #calculates the meter of a line of text.
    if len(text)==0:
        return ''
    #capitalize the text
    s = text.upper()
    #remove any punctuation
    whitelist = set('abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    s2 = ''.join(filter(whitelist.__contains__, s))
    #split the text into individual words
    split_list = re.split('[\s\']', s2)
    # split_list = list(s2.split(" ")) 
    #find the stress for individual words
    line_stress=""
    for word in split_list:
        if len(word)>0:
            if word in stress_dictionary:
                line_stress = line_stress + stress_dictionary[word]
            else:
                line_stress = line_stress + "*"
    return line_stress

def rhyme_check(text1,target_rhyme_list,rhyme_dictionary,reverse_rhyme_dictionary,params):
    #checks whether text1 and target_rhyme_line rhyme according to a pronunciation dictionary.
    global acceptable_punctuation
    global bad_rhymes
    xprint("target_rhyme_list =")
    xprint(target_rhyme_list)
    if len(target_rhyme_list)>0:
        target_rhyme_line = target_rhyme_list[0]
    else:
        target_rhyme_line = ""
    xprint("rhyme_check target_rhyme_line =")
    xprint(target_rhyme_line)
    #remove punctuation and put both in lower case
    text1=text1.strip().lower()
    target_rhyme_line=target_rhyme_line.strip().lower()
    #token 0, which is "!", is code for a line that never will be rhymed with.  
    if target_rhyme_line =="!":
        return True
    #the empty string is code for a line that WILL be rhymed with in the future.
    if target_rhyme_line =="":
        if text1 =="":
            return True
        else:
            #only words that have enough potential rhymes are allowed.
            text1_words = text1.split(" ")
            last_word1 = text1_words[-1]
            if last_word1 in rhyme_dictionary:
                if rhyme_dictionary[last_word1] in reverse_rhyme_dictionary:
                    #print(last_word1)
                    enough_rhymes =  len(reverse_rhyme_dictionary[rhyme_dictionary[last_word1]])>params.rhyme_set_size
                    if enough_rhymes and (not last_word1 in bad_rhymes):         
                        return True
                    else:
                        xprint("! not enough rhymes or last word 1 in bad_rhymes")
                        return False
                else:
                    xprint("! not in reverse dictionary ")
                    return False      
            else:
                #the word isn't in the dictionary or there are not enough other words that rhyme with it.
                xprint("! last word 1 not in rhyme dictionary")
                return False
    else:
        #the two lines need to actually rhyme
        text1_words = text1.split(" ")
        last_word1 = text1_words[-1]
        #remove punctuation from the end of the last words
        regex = re.compile('[^a-zA-Z]')
        last_word1 = regex.sub('', last_word1)
        target_rhyme_line_words = target_rhyme_line.split(" ")
        last_word2 = target_rhyme_line_words[-1]
        #if tokenizer.encode(last_word2[-1])[0] in acceptable_punctuation:
        regex = re.compile('[^a-zA-Z]')
        last_word2 = regex.sub('', last_word2)
        for line in target_rhyme_list:
            target_rhyme_line=line.strip().lower()
            target_rhyme_line_words = target_rhyme_line.split(" ")
            last_word2 = target_rhyme_line_words[-1]
            regex = re.compile('[^a-zA-Z]')
            last_word2 = regex.sub('', last_word2)
            #print(last_word2)
            if last_word1 == last_word2:
                #prevent a word rhyming with itself
                xprint("! a word is rhyming with itself")
                return False
        if (last_word1 in rhyme_dictionary) and (last_word2 in rhyme_dictionary):
            rhyme1 = rhyme_dictionary[last_word1]
            rhyme2 = rhyme_dictionary[last_word2]
            rhyme1 = rhyme1.replace("0","1")
            rhyme2 = rhyme2.replace("0","1")
            #print(rhyme1 + " vs. " +  rhyme2)
            if (rhyme1 == rhyme2):
                return True
            else:
                xprint("! last word1 does not rhyme with last word 2")
                return False
        else:
            xprint("! last word 1 or last word 2 not in rhyme dictionary")
            xprint(last_word1)
            xprint(last_word2)
            return False
       
def compare_meters(test_meter,target_meter):
    #checks whether test_meter is plausibly matching target_meter. test_meter can include unknown ? stresses. 
    matchflag=False
    
    if len(test_meter)>0 and test_meter[-1]=="*":
        test_meter=test_meter[:-1]
    if "*" in test_meter[:-1]:
        return False
    if len(test_meter)<=len(target_meter):
        matchflag=True
        for character1,character2 in zip(test_meter,target_meter):
            if (character1=="`" and character2=="`") or (character1=="~" and character2=="~") or character1=="?":
                pass
            else:
                matchflag=False
    if len(test_meter)==0:
        matchflag = True  
    #If you want to force it to end on a strongly stressed word, uncomment this.
    #elif test_meter[-1] == '?':
    #    matchflag = False  
    return matchflag

def rhyme_and_meter_filter(this_text_sentence,target_rhyme_list,target_meter,probs,params):
    #returns a sorted list of words which are (usually) compatible with the upcoming rhyme and meter constraints.
    #It's meant to make searching faster, not to be a perfect filter
    global stress_tokens
    global big_rhymesets
    global acceptable_punctuation
    global rhyming_tokens
    global syllable_tokens
    #this randomization helps prevent repetition, but it's kind of a hack.
    offset = randint(0,2)
    this_meter = text_to_meter(this_text_sentence,stress_dictionary)
    xprint("target_rhyme_list =")
    xprint(target_rhyme_list)
    if len(target_rhyme_list)>0:
        target_rhyme = target_rhyme_list[0]
    else:
        target_rhyme = target_rhyme_list
    xprint("target_rhyme_list =")
    xprint(target_rhyme_list)
    
    #meter filter
    next_stresses = target_meter[len(this_meter):min(len(this_meter)+3,len(target_meter)+1)]
    if len(next_stresses)==0:
        return []
    all_tokens = set(range(0,50257))
    stress_okay = set(stress_tokens[next_stresses])
    #all tokens EXCEPT those with okay stress or acceptable punctuation are zeroed out.
    for token in all_tokens.difference(stress_okay.union(acceptable_punctuation)):
        probs[token] = 0
   
    #rhyme_filter
    xprint("meter_length = ", end = "")
    xprint(len(this_meter))
    # lower the probability of one-syllable words, to allow longer words to show up.
    too_common_tokens = syllable_tokens[1].union(acceptable_punctuation)
    for t in range(0,50257):
            if t in too_common_tokens:
                probs[t] =probs[t]/params.one_syllable_suppression  
    #"!" is a code for a non-rhyming sentence. "" is code for a sentence that will be rhymed with later.
    if len(target_rhyme)>0 and target_rhyme != "!":
        target_rhyme_words = target_rhyme.split(" ")
        last_target_rhyme_word = target_rhyme_words[-1].strip().lower()     
        if last_target_rhyme_word[-1] in {"!",".",",",";",":","?","-"}:
            last_target_rhyme_word = last_target_rhyme_word[:-1]
        xprint("target rhyme =",end="")
        xprint(last_target_rhyme_word)
        these_rhyming_tokens = rhyming_tokens[last_target_rhyme_word]
        xprint(tokenizer.decode(these_rhyming_tokens))  
        if len(this_meter)==len(target_meter)-1:
            for t in range(0,50257):
                if t in these_rhyming_tokens:
                    pass
                else:
                    probs[t] = 0
        elif len(this_meter)==len(target_meter)-2:
            # either a rhyming word or a one-syllable word which could be followed by a rhyming word is okay.
            safeset = syllable_tokens[1].union(these_rhyming_tokens)
            for t in range(0,50257):
                if t in safeset:
                    pass
                else:
                    probs[t] = 0
        sorted_probability_list = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
        short_probability_list = sorted_probability_list[0+offset:params.ultimate_expansion+offset]
        xprint("PART 1")
    elif len(this_meter)>len(target_meter)-3:
        sorted_probability_list = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
        short_probability_list = sorted_probability_list[0+offset:params.penultimate_expansion+offset]
        xprint("PART 2")
    elif len(this_meter)<1:
        sorted_probability_list = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
        short_probability_list = sorted_probability_list
        xprint("PART 3")
    else:
        sorted_probability_list = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
        short_probability_list = sorted_probability_list[0+offset:params.other_expansion+offset]
        xprint("PART 4")
    short_probability_list = [i for i in short_probability_list if i[1] != 0]
    xprint("short prob list len = ", end =" ")
    xprint(len(short_probability_list))
  
    return short_probability_list

def grow_branches(these_tokens, probs, input_probability,past,params, prompt_length,target_rhyme_list,target_meter):
    #recursive function to find all sentence completions
    xprint("___________________________________________")
    global model
    global tokenizer
    global stress_dictionary
    global rhyme_dictionary
    global reverse_rhyme_dictionary
    global stuck_counter
    global past_backup 
    stuck_counter = stuck_counter + 1
    if stuck_counter > params.stuck_counter_limit:
        params.probability_threshold = params.probability_threshold/2
        stuck_counter = 0
        past = past_backup
        these_tokens = these_tokens[:prompt_length]    
    found = None
    this_text_sentence = tokenizer.decode(these_tokens[prompt_length:])
    if len(these_tokens[prompt_length:])<2:
        probability_threshold = 0 # no restrictions on the first tokens in each line.
    else: 
        probability_threshold = params.probability_threshold
    short_probability_list = rhyme_and_meter_filter(this_text_sentence,target_rhyme_list,target_meter,probs,params)
    #proceed only if there are tokens in the probability list that are sufficiently likely to form a sensible sentence.
    if len(short_probability_list)==0:
        xprint("! len(short_probability_list)==0")
        return False
    else:
        count = 0
        #for (this_token,this_probability) in short_probability_list:
        #    xprint(tokenizer.decode(this_token), end = "|")
        for (this_token,this_probability) in short_probability_list:
            xprint("------------------------------")
            tokens_are_probable_enough_to_continue = this_probability > probability_threshold
            xprint("tokens are probable: ",end = "")
            xprint(tokens_are_probable_enough_to_continue)
            if not tokens_are_probable_enough_to_continue:
                xprint("! tokens_are_not probable_enough_to_continue")
                return False
            else:
                count = count+1
                #the token forms the next extension of the current line.
                next_probability = this_probability * input_probability
                next_tokens = these_tokens.copy()
                next_tokens.append(this_token)
                next_text_sentence = tokenizer.decode(next_tokens[prompt_length:])
                next_meter = text_to_meter(next_text_sentence,stress_dictionary)
                xprint(next_meter)
                if "*" in next_meter[:-1]:
                    xprint("! * in next meter")
                    return False
                meter_check = compare_meters(next_meter,target_meter)
                #print(next_text_sentence)
                if len(next_meter)>len(target_meter):
                    xprint("! len(next_meter)>len(target_meter)")
                    continue
                elif len(next_meter)==len(target_meter):
                #this might be a line we want to keep, so we need to verify that the meter and rhyme are good.
                    if not meter_check:
                        xprint("! not meter check")
                        continue
                    else:
                        rhyme_checks_out = rhyme_check(next_text_sentence,target_rhyme_list,rhyme_dictionary,reverse_rhyme_dictionary,params)
                        if not rhyme_checks_out:
                            xprint("! rhyme doesn't check out")
                            continue
                        else:
                             # the line has completed successfully
                            (word_completion_list,next_past) = expand_node(next_tokens,past)
                            sorted_word_completion_list = sorted(enumerate(word_completion_list), key=lambda x: x[1], reverse=True)
                            # sometimes it generates the first part of a longer word, that happens to be an actual word. This prevents that from messing things up.
                            potential_word_completion = tokenizer.decode(sorted_word_completion_list[0][0])
                            all_tokens = set(range(0,50257))
                            if potential_word_completion[0] in str.ascii_lowercase: #i.e. it starts with a letter instead of a space, so it's continuing a word
                                #print("! potential_word_completion[0] in str.ascii_lowercase")
                                continue                           
                            elif params.line_end_punctuation_constraint == True:
                                (end_punctuation_list,next_past) = (word_completion_list,next_past)
                                for token in all_tokens.difference(end_punctuation):
                                    end_punctuation_list[token] = 0                               
                                sorted_end_punctuation_list = sorted(enumerate(end_punctuation_list), key=lambda x: x[1], reverse=True)
                                punctuation_probability = sorted_end_punctuation_list [0][1]  
                                if punctuation_probability > params.punctuation_probability_threshold:
                                    #success!
                                    end_punctuation_choice = sorted_end_punctuation_list [0][0] 
                                    next_tokens.append(end_punctuation_choice)
                                    next_text_sentence = tokenizer.decode(next_tokens[prompt_length:])
                                    #print("*** " + next_text_sentence + "\t" + next_meter)
                                    return next_tokens[prompt_length:]
                                else:
                                    #print("! end punctuation too rare")
                                    continue
                            else:
                                #success!
                                #print("*** " + next_text_sentence + "\t" + next_meter)
                                return next_tokens[prompt_length:]  
                #If it starts generating strings of punctuation, it rarely recovers. So I put in this hacky check to prevent it.
                punctuation_repeats = (len(these_tokens)>1 and these_tokens[-2] in punctuation and these_tokens[-1] in punctuation) or (len(these_tokens)>0 and these_tokens[-1] in punctuation and this_token in punctuation)
                line_is_way_too_long = (len(these_tokens[prompt_length+1:])>20)
                if next_probability < params.line_probability_threshold or punctuation_repeats or line_is_way_too_long:
                    if len(these_tokens[prompt_length+1:])>1:                       
                        xprint("! len(these_tokens[prompt_length+1:])>1")
                        return False # this returns because if one thing fails the probability check the rest will. Also the repeating punctuation thing needs to be nipped in the bud.
                    else:
                        xprint("! len(these_tokens[prompt_length+1:])<=1")
                        continue #the start of a line gets some leeway so that it doesn't return false and abandon the whole poem.
                else:
                    found = False
                    if meter_check and len(next_meter)<len(target_meter):
                        #this isn't long enough to be a complete line, but it could be the start of a complete line, so we expand it.
                        (next_probability_list,next_past) = expand_node(next_tokens,past)
                        found = grow_branches(next_tokens,next_probability_list, next_probability, next_past,params,prompt_length,target_rhyme_list,target_meter)
                    if found != False:
                        xprint("found =", end ="")
                        xprint(found)
                        return found
    xprint("! end of function")
    return False

def expand_node(sentence, past):
    #finds probabilities for the next token using gpt-2. This is the only computationally expensive operation in the program.
    global model
    if past == None:
        input_ids = torch.tensor(sentence).unsqueeze(0)
    else:
        input_ids = torch.tensor([sentence[-1]]).unsqueeze(0)
    inputs = {'input_ids': input_ids}    
    with torch.no_grad():
        logits, past = model(**inputs, past_key_values=past, return_dict=False)
        # use this line for Huggingface v3: logits, past = model(**inputs, past=past)
        logits[0][0][50256]=-math.inf # no <end of text> token
        logits = logits[:, -1, :]  
        probs = F.softmax(logits, dim=-1).tolist()[0]
        return (probs, past)

def create_stress_dictionary():
    pronounce_file = open("pronounce.txt", "r")
    stress_dictionary = {}
    for line in pronounce_file:
        line = line.strip("\n")
        parts = line.split(" ")
        syllable_list = parts[2:]
        word = parts[0]
        stresses=""
        if word in ["A","AN","THE","AND","BUT","OR"]:
            stresses="~"
        elif word in ["I","YOU","HE","SHE","IT","WE","THEY","MY","HIS","HER","ITS","OUR","YOUR","THEIR","OURS","YOURS","THEIRS","AM","IS","ARE","WAS","WERE","BEEN","BE","HAVE","HAS","HAD","DO","DOES","DID","WILL","WOULD","SHALL","SHOULD","MAY","MIGHT","MUST","CAN","COULD","OF","WITH","AT","FROM","TO","IN","FOR","ON","BY","LIKE","SINCE","UP","OFF","NEAR","WHICH","AS","EACH","SO","THAT","THATS"]:
            stresses="?"    
        else:
            for syllable in syllable_list:
                if syllable.endswith("1"):
                    stresses=stresses+"`"
                elif syllable.endswith("0"):
                    stresses=stresses+"~"
                elif syllable.endswith("2"):
                    stresses=stresses+"?"
        if word in {"A","B","C","D","E","F","G","H","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"}:
            pass
        else:
            stress_dictionary[word] = stresses
    return stress_dictionary

def create_rhyme_dictionary(tokenizer):
    pronounce_file = open("pronounce.txt", "r")
    rhyme_dictionary = {}
    reverse_rhyme_dictionary = {}
    syllable_count_dictionary = {}
    for line in pronounce_file:
        line = line.strip()
        if line.startswith(';'): continue
        word, phones = line.split("  ")
        syllables = phones.split(" ")
        syllable_count_dictionary[word]=phones.count("0")+phones.count("1")+phones.count("2")
        join_flag = 0
        outstring = ''
        for syllable in syllables:
            if join_flag == 0:
                if "1" in syllable:
                    join_flag = 1
                    outstring = syllable
            else:
                outstring = outstring + " " + syllable
        if outstring == "":
            for syllable in syllables:
                if join_flag == 0:
                    if "0" in syllable:
                        join_flag = 1
                        outstring = syllable
                else:
                    outstring = outstring + " " + syllable
        rhyme_dictionary[word.lower()] = outstring
        if outstring in reverse_rhyme_dictionary:
            reverse_rhyme_dictionary[outstring].append(word.lower())
        else:
            reverse_rhyme_dictionary[outstring]=[word.lower()]
    
    rhyming_tokens = pickle.load( open( "rhyming_tokens.p", "rb" ) )
    syllable_tokens = pickle.load( open( "syllable_tokens.p", "rb" ) )
    
    bad_rhymes = ["a","an","it","is","as","at","was","of","at","that",
                     "has","your","my","his","their","on","for","its","to",
                     "from","if","ur","re","our","un","dis","diss","mis",
                     "wat","com","comm","psych","lol","vis","al","los","pol",
                     "bis","up", " la","sa","ha","mah", " wal", "lat", "ot", "sol",
                     "b","c","d","e","f","g","h","i","j","k","l","m",
                     "n","o","p","q","r","s","t","u","v","w","x","y","z"]
    return rhyme_dictionary, reverse_rhyme_dictionary, bad_rhymes, syllable_count_dictionary, rhyming_tokens, syllable_tokens

def poem_scheme(kind):
    #in "rhyme_scheme" the first thing in the list for each line must be the line you want to rhyme with. 
    # After that you can list other lines you want to avoid repeating the last word.
    # "meter_scheme" is ` for accented, ~ for unaccented syllable. 
    global poem_line
    if kind == "limerick":
        number_of_lines = 5
        meter_scheme = [""] * number_of_lines
        for line in {0,1,4}:
            meter_scheme[line] = "~`~~`~~`" 
        for line in {2,3}:
            meter_scheme[line] = "~`~~`"
        rhyme_scheme = [ "", [poem_line[0]], "", [poem_line[2]], [poem_line[0], poem_line[1]] ]
    if kind == "sonnet":
        number_of_lines = 10
        meter_scheme = [""] * number_of_lines
        for line in range(0,number_of_lines):
            meter_scheme[line] = "~`~`~`~`~`"
        rhyme_scheme = ["","",[poem_line[0]],[poem_line[1]],"","",[poem_line[4]],[poem_line[5]],"",[poem_line[8]] ]
    if kind == "blank verse":
        number_of_lines = 10
        meter_scheme = [""] * number_of_lines
        for line in range(0,number_of_lines):
            meter_scheme[line] = "~`~`~`~`~`"
        rhyme_scheme = [[0]]*number_of_lines
    if kind == "couplets":
        number_of_lines = 10
        meter_scheme = [""] * number_of_lines
        for line in range(0,number_of_lines):
            meter_scheme[line] = "`~`~`~"
        rhyme_scheme = ["",[poem_line[0]],"",[poem_line[2]],"",[poem_line[4]],"",[poem_line[6]],"",[poem_line[8]] ]
    if kind == "mini-couplets":
        number_of_lines = 20
        meter_scheme = [""] * number_of_lines
        for line in range(0,number_of_lines):
            meter_scheme[line] = "~`~`"
        rhyme_scheme = ["",[poem_line[0]],"",[poem_line[2]],"",[poem_line[4]],"",[poem_line[6]],"",[poem_line[8]],"",[poem_line[10]],"",[poem_line[12]],"",[poem_line[14]],"",[poem_line[16]],"",[poem_line[18]] ]
        params.penultimate_expansion = 10000
    if kind == "ballad":
        number_of_lines = 16
        meter_scheme = [""] * number_of_lines
        for line in {0,2,4,6,8,10,12,14}:
            meter_scheme[line] = "~`~`~`~`"
        for line in {1,3,5,7,9,11,13,15}:
            meter_scheme[line] = "~`~`~`"
        rhyme_scheme = [[0],"",[0],[poem_line[1]],[0],"",[0],[poem_line[5]],[0],"",[0],[poem_line[9]],[0],"",[0],[poem_line[13]]]
    return number_of_lines, rhyme_scheme, meter_scheme
            
#-----------------------------------------------

tokenizer = GPT2Tokenizer.from_pretrained('gpt2') 

def init_limerick_generator():
  global rhyme_dictionary
  global reverse_rhyme_dictionary
  global bad_rhymes
  global syllable_count_dictionary
  global rhyming_tokens
  global syllable_tokens
  global stress_dictionary
  global stress_tokens

  rhyme_dictionary, reverse_rhyme_dictionary, bad_rhymes, syllable_count_dictionary, rhyming_tokens, syllable_tokens = create_rhyme_dictionary(tokenizer)
  stress_dictionary = create_stress_dictionary()   
  stress_tokens = pickle.load( open("stress_tokens.p", "rb"))

def generate_limerick(prompt, input_model):
    global rhyme_dictionary
    global reverse_rhyme_dictionary
    global bad_rhymes
    global syllable_count_dictionary
    global rhyming_tokens
    global syllable_tokens
    global stress_dictionary
    global stress_tokens
    global model
    global poem_line
    global stuck_counter


    model = input_model
    
    with torch.no_grad():
        raw_prompt = prompt
        prompt = tokenizer.encode(raw_prompt)
        original_length = len(prompt)
        past = None
        (probs, past) = expand_node(prompt, None) 
        scheme = "limerick"
        poem_line = [""] * 100000 #this just has to be long enough the next line will never complain-- fixed two lines down
        number_of_lines, rhyme_scheme, meter_scheme = poem_scheme(scheme)
        poem_line = [""] * number_of_lines  
        line = 0
        backup_prompts = [""]*100
        backup_pasts = [""]*100
        while line < number_of_lines:
            stuck_counter = 0
            backup_prompts[line]=prompt
            backup_pasts[line]=past
            number_of_lines, rhyme_scheme, meter_scheme = poem_scheme(scheme)
            target_rhyme_list = []
            for target_rhyme_line in rhyme_scheme[line]:
                target_rhyme_list.append(tokenizer.decode(target_rhyme_line))
            if target_rhyme_list == []:
                target_rhyme_list = ""
            xprint(target_rhyme_list)
            target_meter = meter_scheme[line]
            this_line = grow_branches(prompt,probs,1,past,params,len(prompt),target_rhyme_list,target_meter)
            if this_line == False:
                print("something went wrong, quitting")
                break
            poem_line[line] = this_line
            line = line + 1
            prompt = prompt  + this_line
            past_backup = past
            (probs, past) = expand_node(prompt, None) 
        # this just changes the last token to a period. Very hacky.
        if poem_line[-1][-1] in end_punctuation:
            poem_line[-1][-1] = tokenizer.encode('.')[0]
        #print()
        #print(tokenizer.decode(prompt[original_length:]))
        #print()
        s = tokenizer.decode(poem_line[0])
        poem_for_gruen = raw_prompt + s + '\n'

        for line in range(1,number_of_lines):
            if poem_line[line][0] in acceptable_punctuation:
                poem_line[line-1].append(poem_line[line][0])
                poem_line[line] = poem_line[line][1:]
        for line in range(1,number_of_lines):
            s = tokenizer.decode(poem_line[line])
            poem_for_gruen += s + '\n'
        
        print("*" * 12)

        poem_for_gruen = [poem_for_gruen]
            
        return poem_for_gruen

def ram_gruen(text):
  return gruen.get_gruen([text])  
