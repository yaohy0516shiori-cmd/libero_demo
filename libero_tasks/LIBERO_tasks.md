# LIBERO task list

Rendered from Armory's pinned LIBERO (init state 0, after 30 settle steps). Each image: left = agent-view camera, right = wrist camera.

> Why 30 steps: LIBERO's own evaluation waits 5 zero-action steps and Armory waits 10. Over all 130 tasks (init state 0), the scene first becomes quiet at a median of 13 steps and at the latest by step 29 (`libero_test/audit/results_all_tasks`); at step 30 every task is quiet. At step 10, 17 tasks still have objects in mid-air, so those frames silently omit objects (`libero_test/audit/results_render_check/wait_10_vs_30.png`).

## libero_spatial (10 tasks)

same objects, different spatial layouts (tests spatial reasoning).

Scenes: LIBERO_Tabletop_Manipulation ×10

Fixtures: flat_stove_1, main_table, wooden_cabinet_1

Contact sheet: `sheet_libero_spatial.png`

| id | scene | instruction | init states | image |
|---|---|---|---|---|
| 0 | LIBERO_Tabletop_Manipulation | pick up the black bowl between the plate and the ramekin and place it on the plate | 50 | `img/libero_spatial_00.png` |
| 1 | LIBERO_Tabletop_Manipulation | pick up the black bowl next to the ramekin and place it on the plate | 50 | `img/libero_spatial_01.png` |
| 2 | LIBERO_Tabletop_Manipulation | pick up the black bowl from table center and place it on the plate | 50 | `img/libero_spatial_02.png` |
| 3 | LIBERO_Tabletop_Manipulation | pick up the black bowl on the cookie box and place it on the plate | 50 | `img/libero_spatial_03.png` |
| 4 | LIBERO_Tabletop_Manipulation | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate | 50 | `img/libero_spatial_04.png` |
| 5 | LIBERO_Tabletop_Manipulation | pick up the black bowl on the ramekin and place it on the plate | 50 | `img/libero_spatial_05.png` |
| 6 | LIBERO_Tabletop_Manipulation | pick up the black bowl next to the cookie box and place it on the plate | 50 | `img/libero_spatial_06.png` |
| 7 | LIBERO_Tabletop_Manipulation | pick up the black bowl on the stove and place it on the plate | 50 | `img/libero_spatial_07.png` |
| 8 | LIBERO_Tabletop_Manipulation | pick up the black bowl next to the plate and place it on the plate | 50 | `img/libero_spatial_08.png` |
| 9 | LIBERO_Tabletop_Manipulation | pick up the black bowl on the wooden cabinet and place it on the plate | 50 | `img/libero_spatial_09.png` |

## libero_object (10 tasks)

same layout, different target objects (tests object recognition).

Scenes: LIBERO_Floor_Manipulation ×10

Fixtures: floor

Contact sheet: `sheet_libero_object.png`

| id | scene | instruction | init states | image |
|---|---|---|---|---|
| 0 | LIBERO_Floor_Manipulation | pick up the alphabet soup and place it in the basket | 50 | `img/libero_object_00.png` |
| 1 | LIBERO_Floor_Manipulation | pick up the cream cheese and place it in the basket | 50 | `img/libero_object_01.png` |
| 2 | LIBERO_Floor_Manipulation | pick up the salad dressing and place it in the basket | 50 | `img/libero_object_02.png` |
| 3 | LIBERO_Floor_Manipulation | pick up the bbq sauce and place it in the basket | 50 | `img/libero_object_03.png` |
| 4 | LIBERO_Floor_Manipulation | pick up the ketchup and place it in the basket | 50 | `img/libero_object_04.png` |
| 5 | LIBERO_Floor_Manipulation | pick up the tomato sauce and place it in the basket | 50 | `img/libero_object_05.png` |
| 6 | LIBERO_Floor_Manipulation | pick up the butter and place it in the basket | 50 | `img/libero_object_06.png` |
| 7 | LIBERO_Floor_Manipulation | pick up the milk and place it in the basket | 50 | `img/libero_object_07.png` |
| 8 | LIBERO_Floor_Manipulation | pick up the chocolate pudding and place it in the basket | 50 | `img/libero_object_08.png` |
| 9 | LIBERO_Floor_Manipulation | pick up the orange juice and place it in the basket | 50 | `img/libero_object_09.png` |

## libero_goal (10 tasks)

same scene and objects, different goals (tests goal/instruction following).

Scenes: LIBERO_Tabletop_Manipulation ×10

Fixtures: flat_stove_1, main_table, wine_rack_1, wooden_cabinet_1

Contact sheet: `sheet_libero_goal.png`

| id | scene | instruction | init states | image |
|---|---|---|---|---|
| 0 | LIBERO_Tabletop_Manipulation | open the middle drawer of the cabinet | 50 | `img/libero_goal_00.png` |
| 1 | LIBERO_Tabletop_Manipulation | put the bowl on the stove | 50 | `img/libero_goal_01.png` |
| 2 | LIBERO_Tabletop_Manipulation | put the wine bottle on top of the cabinet | 50 | `img/libero_goal_02.png` |
| 3 | LIBERO_Tabletop_Manipulation | open the top drawer and put the bowl inside | 50 | `img/libero_goal_03.png` |
| 4 | LIBERO_Tabletop_Manipulation | put the bowl on top of the cabinet | 50 | `img/libero_goal_04.png` |
| 5 | LIBERO_Tabletop_Manipulation | push the plate to the front of the stove | 50 | `img/libero_goal_05.png` |
| 6 | LIBERO_Tabletop_Manipulation | put the cream cheese in the bowl | 50 | `img/libero_goal_06.png` |
| 7 | LIBERO_Tabletop_Manipulation | turn on the stove | 50 | `img/libero_goal_07.png` |
| 8 | LIBERO_Tabletop_Manipulation | put the bowl on the plate | 50 | `img/libero_goal_08.png` |
| 9 | LIBERO_Tabletop_Manipulation | put the wine bottle on the rack | 50 | `img/libero_goal_09.png` |

## libero_10 (10 tasks)

long-horizon, multi-step tasks across varied scenes (a.k.a. LIBERO-Long).

Scenes: KITCHEN_SCENE3 ×1, KITCHEN_SCENE4 ×1, KITCHEN_SCENE6 ×1, KITCHEN_SCENE8 ×1, LIVING_ROOM_SCENE1 ×1, LIVING_ROOM_SCENE2 ×2, LIVING_ROOM_SCENE5 ×1, LIVING_ROOM_SCENE6 ×1, STUDY_SCENE1 ×1

Fixtures: desk_caddy_1, flat_stove_1, kitchen_table, living_room_table, microwave_1, study_table, white_cabinet_1, wine_rack_1

Contact sheet: `sheet_libero_10.png`

| id | scene | instruction | init states | image |
|---|---|---|---|---|
| 0 | LIVING_ROOM_SCENE2 | put both the alphabet soup and the tomato sauce in the basket | 50 | `img/libero_10_00.png` |
| 1 | LIVING_ROOM_SCENE2 | put both the cream cheese box and the butter in the basket | 50 | `img/libero_10_01.png` |
| 2 | KITCHEN_SCENE3 | turn on the stove and put the moka pot on it | 50 | `img/libero_10_02.png` |
| 3 | KITCHEN_SCENE4 | put the black bowl in the bottom drawer of the cabinet and close it | 50 | `img/libero_10_03.png` |
| 4 | LIVING_ROOM_SCENE5 | put the white mug on the left plate and put the yellow and white mug on the right plate | 50 | `img/libero_10_04.png` |
| 5 | STUDY_SCENE1 | pick up the book and place it in the back compartment of the caddy | 50 | `img/libero_10_05.png` |
| 6 | LIVING_ROOM_SCENE6 | put the white mug on the plate and put the chocolate pudding to the right of the plate | 50 | `img/libero_10_06.png` |
| 7 | LIVING_ROOM_SCENE1 | put both the alphabet soup and the cream cheese box in the basket | 50 | `img/libero_10_07.png` |
| 8 | KITCHEN_SCENE8 | put both moka pots on the stove | 50 | `img/libero_10_08.png` |
| 9 | KITCHEN_SCENE6 | put the yellow and white mug in the microwave and close it | 50 | `img/libero_10_09.png` |

## libero_90 (90 tasks)

90 short-horizon tasks across kitchen / living-room / study scenes (pretraining set).

Scenes: KITCHEN_SCENE1 ×5, KITCHEN_SCENE10 ×6, KITCHEN_SCENE2 ×7, KITCHEN_SCENE3 ×4, KITCHEN_SCENE4 ×6, KITCHEN_SCENE5 ×5, KITCHEN_SCENE6 ×2, KITCHEN_SCENE7 ×3, KITCHEN_SCENE8 ×2, KITCHEN_SCENE9 ×6, LIVING_ROOM_SCENE1 ×4, LIVING_ROOM_SCENE2 ×5, LIVING_ROOM_SCENE3 ×5, LIVING_ROOM_SCENE4 ×5, LIVING_ROOM_SCENE5 ×4, LIVING_ROOM_SCENE6 ×4, STUDY_SCENE1 ×4, STUDY_SCENE2 ×4, STUDY_SCENE3 ×5, STUDY_SCENE4 ×4

Fixtures: desk_caddy_1, flat_stove_1, kitchen_table, living_room_table, microwave_1, study_table, white_cabinet_1, wine_rack_1, wooden_cabinet_1, wooden_two_layer_shelf_1

Contact sheet: `sheet_libero_90.png`

| id | scene | instruction | init states | image |
|---|---|---|---|---|
| 0 | KITCHEN_SCENE10 | close the top drawer of the cabinet | 50 | `img/libero_90_00.png` |
| 1 | KITCHEN_SCENE10 | close the top drawer of the cabinet and put the black bowl on top of it | 50 | `img/libero_90_01.png` |
| 2 | KITCHEN_SCENE10 | put the black bowl in the top drawer of the cabinet | 50 | `img/libero_90_02.png` |
| 3 | KITCHEN_SCENE10 | put the butter at the back in the top drawer of the cabinet and close it | 50 | `img/libero_90_03.png` |
| 4 | KITCHEN_SCENE10 | put the butter at the front in the top drawer of the cabinet and close it | 50 | `img/libero_90_04.png` |
| 5 | KITCHEN_SCENE10 | put the chocolate pudding in the top drawer of the cabinet and close it | 50 | `img/libero_90_05.png` |
| 6 | KITCHEN_SCENE1 | open the bottom drawer of the cabinet | 50 | `img/libero_90_06.png` |
| 7 | KITCHEN_SCENE1 | open the top drawer of the cabinet | 50 | `img/libero_90_07.png` |
| 8 | KITCHEN_SCENE1 | open the top drawer of the cabinet and put the bowl in it | 50 | `img/libero_90_08.png` |
| 9 | KITCHEN_SCENE1 | put the black bowl on the plate | 50 | `img/libero_90_09.png` |
| 10 | KITCHEN_SCENE1 | put the black bowl on top of the cabinet | 50 | `img/libero_90_10.png` |
| 11 | KITCHEN_SCENE2 | open the top drawer of the cabinet | 50 | `img/libero_90_11.png` |
| 12 | KITCHEN_SCENE2 | put the black bowl at the back on the plate | 50 | `img/libero_90_12.png` |
| 13 | KITCHEN_SCENE2 | put the black bowl at the front on the plate | 50 | `img/libero_90_13.png` |
| 14 | KITCHEN_SCENE2 | put the middle black bowl on the plate | 50 | `img/libero_90_14.png` |
| 15 | KITCHEN_SCENE2 | put the middle black bowl on top of the cabinet | 50 | `img/libero_90_15.png` |
| 16 | KITCHEN_SCENE2 | stack the black bowl at the front on the black bowl in the middle | 50 | `img/libero_90_16.png` |
| 17 | KITCHEN_SCENE2 | stack the middle black bowl on the back black bowl | 50 | `img/libero_90_17.png` |
| 18 | KITCHEN_SCENE3 | put the frying pan on the stove | 50 | `img/libero_90_18.png` |
| 19 | KITCHEN_SCENE3 | put the moka pot on the stove | 50 | `img/libero_90_19.png` |
| 20 | KITCHEN_SCENE3 | turn on the stove | 50 | `img/libero_90_20.png` |
| 21 | KITCHEN_SCENE3 | turn on the stove and put the frying pan on it | 50 | `img/libero_90_21.png` |
| 22 | KITCHEN_SCENE4 | close the bottom drawer of the cabinet | 50 | `img/libero_90_22.png` |
| 23 | KITCHEN_SCENE4 | close the bottom drawer of the cabinet and open the top drawer | 50 | `img/libero_90_23.png` |
| 24 | KITCHEN_SCENE4 | put the black bowl in the bottom drawer of the cabinet | 50 | `img/libero_90_24.png` |
| 25 | KITCHEN_SCENE4 | put the black bowl on top of the cabinet | 50 | `img/libero_90_25.png` |
| 26 | KITCHEN_SCENE4 | put the wine bottle in the bottom drawer of the cabinet | 50 | `img/libero_90_26.png` |
| 27 | KITCHEN_SCENE4 | put the wine bottle on the wine rack | 50 | `img/libero_90_27.png` |
| 28 | KITCHEN_SCENE5 | close the top drawer of the cabinet | 50 | `img/libero_90_28.png` |
| 29 | KITCHEN_SCENE5 | put the black bowl in the top drawer of the cabinet | 50 | `img/libero_90_29.png` |
| 30 | KITCHEN_SCENE5 | put the black bowl on the plate | 50 | `img/libero_90_30.png` |
| 31 | KITCHEN_SCENE5 | put the black bowl on top of the cabinet | 50 | `img/libero_90_31.png` |
| 32 | KITCHEN_SCENE5 | put the ketchup in the top drawer of the cabinet | 50 | `img/libero_90_32.png` |
| 33 | KITCHEN_SCENE6 | close the microwave | 50 | `img/libero_90_33.png` |
| 34 | KITCHEN_SCENE6 | put the yellow and white mug to the front of the white mug | 50 | `img/libero_90_34.png` |
| 35 | KITCHEN_SCENE7 | open the microwave | 50 | `img/libero_90_35.png` |
| 36 | KITCHEN_SCENE7 | put the white bowl on the plate | 50 | `img/libero_90_36.png` |
| 37 | KITCHEN_SCENE7 | put the white bowl to the right of the plate | 50 | `img/libero_90_37.png` |
| 38 | KITCHEN_SCENE8 | put the right moka pot on the stove | 50 | `img/libero_90_38.png` |
| 39 | KITCHEN_SCENE8 | turn off the stove | 50 | `img/libero_90_39.png` |
| 40 | KITCHEN_SCENE9 | put the frying pan on the cabinet shelf | 50 | `img/libero_90_40.png` |
| 41 | KITCHEN_SCENE9 | put the frying pan on top of the cabinet | 50 | `img/libero_90_41.png` |
| 42 | KITCHEN_SCENE9 | put the frying pan under the cabinet shelf | 50 | `img/libero_90_42.png` |
| 43 | KITCHEN_SCENE9 | put the white bowl on top of the cabinet | 50 | `img/libero_90_43.png` |
| 44 | KITCHEN_SCENE9 | turn on the stove | 50 | `img/libero_90_44.png` |
| 45 | KITCHEN_SCENE9 | turn on the stove and put the frying pan on it | 50 | `img/libero_90_45.png` |
| 46 | LIVING_ROOM_SCENE1 | pick up the alphabet soup and put it in the basket | 50 | `img/libero_90_46.png` |
| 47 | LIVING_ROOM_SCENE1 | pick up the cream cheese box and put it in the basket | 50 | `img/libero_90_47.png` |
| 48 | LIVING_ROOM_SCENE1 | pick up the ketchup and put it in the basket | 50 | `img/libero_90_48.png` |
| 49 | LIVING_ROOM_SCENE1 | pick up the tomato sauce and put it in the basket | 50 | `img/libero_90_49.png` |
| 50 | LIVING_ROOM_SCENE2 | pick up the alphabet soup and put it in the basket | 50 | `img/libero_90_50.png` |
| 51 | LIVING_ROOM_SCENE2 | pick up the butter and put it in the basket | 50 | `img/libero_90_51.png` |
| 52 | LIVING_ROOM_SCENE2 | pick up the milk and put it in the basket | 50 | `img/libero_90_52.png` |
| 53 | LIVING_ROOM_SCENE2 | pick up the orange juice and put it in the basket | 50 | `img/libero_90_53.png` |
| 54 | LIVING_ROOM_SCENE2 | pick up the tomato sauce and put it in the basket | 50 | `img/libero_90_54.png` |
| 55 | LIVING_ROOM_SCENE3 | pick up the alphabet soup and put it in the tray | 50 | `img/libero_90_55.png` |
| 56 | LIVING_ROOM_SCENE3 | pick up the butter and put it in the tray | 50 | `img/libero_90_56.png` |
| 57 | LIVING_ROOM_SCENE3 | pick up the cream cheese and put it in the tray | 50 | `img/libero_90_57.png` |
| 58 | LIVING_ROOM_SCENE3 | pick up the ketchup and put it in the tray | 50 | `img/libero_90_58.png` |
| 59 | LIVING_ROOM_SCENE3 | pick up the tomato sauce and put it in the tray | 50 | `img/libero_90_59.png` |
| 60 | LIVING_ROOM_SCENE4 | pick up the black bowl on the left and put it in the tray | 50 | `img/libero_90_60.png` |
| 61 | LIVING_ROOM_SCENE4 | pick up the chocolate pudding and put it in the tray | 50 | `img/libero_90_61.png` |
| 62 | LIVING_ROOM_SCENE4 | pick up the salad dressing and put it in the tray | 50 | `img/libero_90_62.png` |
| 63 | LIVING_ROOM_SCENE4 | stack the left bowl on the right bowl and place them in the tray | 50 | `img/libero_90_63.png` |
| 64 | LIVING_ROOM_SCENE4 | stack the right bowl on the left bowl and place them in the tray | 50 | `img/libero_90_64.png` |
| 65 | LIVING_ROOM_SCENE5 | put the red mug on the left plate | 50 | `img/libero_90_65.png` |
| 66 | LIVING_ROOM_SCENE5 | put the red mug on the right plate | 50 | `img/libero_90_66.png` |
| 67 | LIVING_ROOM_SCENE5 | put the white mug on the left plate | 50 | `img/libero_90_67.png` |
| 68 | LIVING_ROOM_SCENE5 | put the yellow and white mug on the right plate | 50 | `img/libero_90_68.png` |
| 69 | LIVING_ROOM_SCENE6 | put the chocolate pudding to the left of the plate | 50 | `img/libero_90_69.png` |
| 70 | LIVING_ROOM_SCENE6 | put the chocolate pudding to the right of the plate | 50 | `img/libero_90_70.png` |
| 71 | LIVING_ROOM_SCENE6 | put the red mug on the plate | 50 | `img/libero_90_71.png` |
| 72 | LIVING_ROOM_SCENE6 | put the white mug on the plate | 50 | `img/libero_90_72.png` |
| 73 | STUDY_SCENE1 | pick up the book and place it in the front compartment of the caddy | 50 | `img/libero_90_73.png` |
| 74 | STUDY_SCENE1 | pick up the book and place it in the left compartment of the caddy | 50 | `img/libero_90_74.png` |
| 75 | STUDY_SCENE1 | pick up the book and place it in the right compartment of the caddy | 50 | `img/libero_90_75.png` |
| 76 | STUDY_SCENE1 | pick up the yellow and white mug and place it to the right of the caddy | 50 | `img/libero_90_76.png` |
| 77 | STUDY_SCENE2 | pick up the book and place it in the back compartment of the caddy | 50 | `img/libero_90_77.png` |
| 78 | STUDY_SCENE2 | pick up the book and place it in the front compartment of the caddy | 50 | `img/libero_90_78.png` |
| 79 | STUDY_SCENE2 | pick up the book and place it in the left compartment of the caddy | 50 | `img/libero_90_79.png` |
| 80 | STUDY_SCENE2 | pick up the book and place it in the right compartment of the caddy | 50 | `img/libero_90_80.png` |
| 81 | STUDY_SCENE3 | pick up the book and place it in the front compartment of the caddy | 50 | `img/libero_90_81.png` |
| 82 | STUDY_SCENE3 | pick up the book and place it in the left compartment of the caddy | 50 | `img/libero_90_82.png` |
| 83 | STUDY_SCENE3 | pick up the book and place it in the right compartment of the caddy | 50 | `img/libero_90_83.png` |
| 84 | STUDY_SCENE3 | pick up the red mug and place it to the right of the caddy | 50 | `img/libero_90_84.png` |
| 85 | STUDY_SCENE3 | pick up the white mug and place it to the right of the caddy | 50 | `img/libero_90_85.png` |
| 86 | STUDY_SCENE4 | pick up the book in the middle and place it on the cabinet shelf | 50 | `img/libero_90_86.png` |
| 87 | STUDY_SCENE4 | pick up the book on the left and place it on top of the shelf | 50 | `img/libero_90_87.png` |
| 88 | STUDY_SCENE4 | pick up the book on the right and place it on the cabinet shelf | 50 | `img/libero_90_88.png` |
| 89 | STUDY_SCENE4 | pick up the book on the right and place it under the cabinet shelf | 50 | `img/libero_90_89.png` |
