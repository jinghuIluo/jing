# 生图提示词模板

每张图单独生成。根据正文内容替换变量，不要把多张图拼在一起。

```text
Generate one standalone 16:9 horizontal Chinese article illustration.

Visual DNA:
Pure white background. Minimalist black hand-drawn line art. Slightly wobbly pen lines. Lots of empty white space. Sparse red/orange/blue handwritten Chinese annotations. Clean absurd product-sketch feeling. No gradients, no shadows, no paper texture, no complex background, no commercial vector style, no PPT infographic look, no cute mascot poster, no children's illustration, no realistic UI.

Input image required:
Use `assets/character/ian-character-sheet.png` as the canonical character identity and design reference. Pass it to image generation with `referenced_image_paths`. If other images are also provided, label this sheet specifically as the character reference.

Recurring IP character required:
Ian 本人卡通人物, based faithfully on the approved character sheet: an adult Chinese man with short slightly spiky black hair and irregular fringe, straight dark eyebrows, almond-shaped dark eyes, broad rounded face with a defined jaw, medium-width nose, neutral closed lips, subtle moustache and chin stubble, black crew-neck T-shirt, simple black trousers, compact hand-drawn body, slightly oversized but non-chibi head, calm serious deadpan expression. Preserve the same recognizable identity across every pose and image. He must perform the core conceptual action, not decorate the scene. Keep him capable, understated, mildly absurd, and never cute.

Theme:
{正文配图主题}

Structure type:
{结构类型：Workflow / 系统局部 / 前后对比 / 角色状态 / 概念隐喻 / 方法分层 / 地图路线 / 小漫画分镜}

Core idea:
{这张图要表达的核心意思}

Composition:
{具体画面：Ian 本人卡通人物在哪里、正在做什么、主要物件是什么、信息如何流动}

Suggested elements:
{元素1} / {元素2} / {元素3} / {元素4}

Chinese handwritten labels:
{标注词1} / {标注词2} / {标注词3} / {标注词4} / {可选标注词5}

Color use:
Black for main line art, the character's hair, T-shirt and trousers. Use a restrained flat skin tone only on the face and hands. Orange for main flow/path/arrows. Red only for key warnings/problems/results. Blue only for secondary notes or feedback/system state.

Constraints:
One image explains only one core structure. Keep the main subject around 40%-60% of the canvas. Preserve at least 35% blank white space. Use at most 5-8 short handwritten Chinese labels. Do not write a title in the top-left corner. Do not write the structure type on the image. Do not make it a formal diagram, course slide, or dense explainer. Do not copy prior examples or reuse known case compositions unless explicitly requested; invent a fresh visual metaphor for this specific article. It should be clear but not instructional, interesting but not childish, strange but clean.
```

## 图像编辑提示

去掉左上角标题：

```text
Edit the provided image. Remove only the handwritten title "{要删除的文字}" and its underline from the top-left corner. Fill that area with the same clean white background, matching the surrounding blank paper. Preserve everything else exactly: characters, labels, paths, line style, composition, aspect ratio, and image quality. Do not add any new text or objects.
```

增强怪诞感：

```text
Regenerate this illustration with the same core meaning and simple layout, but make the approved Ian cartoon character more central to the conceptual action. Preserve his identity and design from the character sheet. He should be doing the strange work that explains the idea, not standing beside the diagram. Keep it clean, sparse, hand-drawn, deadpan, and not cute.
```
