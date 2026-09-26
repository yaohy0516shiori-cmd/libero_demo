# Settling summary

A step is quiet when linear speed < 1e-3 m/s, angular speed < 1e-2 rad/s and dynamic penetration < 1e-4 m. A case is confirmed once it has been quiet for `window` consecutive steps.

## Overall

| Item | Value |
|---|---|
| cases | 130 |
| failed | 0 |
| never_confirmed | 0 |
| unstable_at_end | 0 |
| quiet_at_step10 | 25 |
| min_step | 24 |
| median_step | 32.0 |
| p95_step | 40.0 |
| max_step | 48 |
| max_sim_s | 2.4 |

## Per suite

| Suite | Cases | Failed | Never confirmed | Quiet at step 10 | Min | Median | P95 | Max (confirmed step) | Max sim. s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| libero_spatial | 10 | 0 | 0 | 1 | 29 | 34.0 | 44.849999999999994 | 48 | 2.4 |
| libero_object | 10 | 0 | 0 | 1 | 28 | 32.0 | 39.0 | 39 | 1.95 |
| libero_goal | 10 | 0 | 0 | 2 | 27 | 31.5 | 36.3 | 39 | 1.95 |
| libero_90 | 90 | 0 | 0 | 21 | 24 | 32.0 | 40.0 | 42 | 2.1 |
| libero_10 | 10 | 0 | 0 | 0 | 33 | 35.0 | 39.0 | 39 | 1.95 |

## Per case

| Suite | Task | Init | First quiet step | Confirmed step | Sim. s | Stable at end | Quiet at step 10 | Initial penetration (m) | Task name |
|---|---:|---:|---:|---:|---:|---|---|---:|---|
| libero_spatial | 0 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | pick_up_the_black_bowl_between_the_plate_and_the_ramekin_and_place_it_on_the_plate |
| libero_spatial | 1 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | pick_up_the_black_bowl_next_to_the_ramekin_and_place_it_on_the_plate |
| libero_spatial | 2 | 0 | 10 | 29 | 1.45 | True | True | 0.00000 | pick_up_the_black_bowl_from_table_center_and_place_it_on_the_plate |
| libero_spatial | 3 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | pick_up_the_black_bowl_on_the_cookie_box_and_place_it_on_the_plate |
| libero_spatial | 4 | 0 | 20 | 39 | 1.95 | True | False | 0.00000 | pick_up_the_black_bowl_in_the_top_drawer_of_the_wooden_cabinet_and_place_it_on_the_plate |
| libero_spatial | 5 | 0 | 29 | 48 | 2.4 | True | False | 0.00000 | pick_up_the_black_bowl_on_the_ramekin_and_place_it_on_the_plate |
| libero_spatial | 6 | 0 | 21 | 40 | 2.0 | True | False | 0.00000 | pick_up_the_black_bowl_next_to_the_cookie_box_and_place_it_on_the_plate |
| libero_spatial | 7 | 0 | 17 | 36 | 1.8 | True | False | 0.00000 | pick_up_the_black_bowl_on_the_stove_and_place_it_on_the_plate |
| libero_spatial | 8 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | pick_up_the_black_bowl_next_to_the_plate_and_place_it_on_the_plate |
| libero_spatial | 9 | 0 | 22 | 41 | 2.05 | True | False | 0.00000 | pick_up_the_black_bowl_on_the_wooden_cabinet_and_place_it_on_the_plate |
| libero_object | 0 | 0 | 13 | 32 | 1.6 | True | False | 0.00048 | pick_up_the_alphabet_soup_and_place_it_in_the_basket |
| libero_object | 1 | 0 | 15 | 34 | 1.7 | True | False | 0.00048 | pick_up_the_cream_cheese_and_place_it_in_the_basket |
| libero_object | 2 | 0 | 11 | 30 | 1.5 | True | False | 0.00048 | pick_up_the_salad_dressing_and_place_it_in_the_basket |
| libero_object | 3 | 0 | 20 | 39 | 1.95 | True | False | 0.00048 | pick_up_the_bbq_sauce_and_place_it_in_the_basket |
| libero_object | 4 | 0 | 20 | 39 | 1.95 | True | False | 0.00048 | pick_up_the_ketchup_and_place_it_in_the_basket |
| libero_object | 5 | 0 | 9 | 28 | 1.4 | True | True | 0.00025 | pick_up_the_tomato_sauce_and_place_it_in_the_basket |
| libero_object | 6 | 0 | 12 | 31 | 1.55 | True | False | 0.00025 | pick_up_the_butter_and_place_it_in_the_basket |
| libero_object | 7 | 0 | 13 | 32 | 1.6 | True | False | 0.00048 | pick_up_the_milk_and_place_it_in_the_basket |
| libero_object | 8 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | pick_up_the_chocolate_pudding_and_place_it_in_the_basket |
| libero_object | 9 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | pick_up_the_orange_juice_and_place_it_in_the_basket |
| libero_goal | 0 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | open_the_middle_drawer_of_the_cabinet |
| libero_goal | 1 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | put_the_bowl_on_the_stove |
| libero_goal | 2 | 0 | 12 | 31 | 1.55 | True | False | 0.00000 | put_the_wine_bottle_on_top_of_the_cabinet |
| libero_goal | 3 | 0 | 12 | 31 | 1.55 | True | False | 0.00000 | open_the_top_drawer_and_put_the_bowl_inside |
| libero_goal | 4 | 0 | 10 | 29 | 1.45 | True | True | 0.00000 | put_the_bowl_on_top_of_the_cabinet |
| libero_goal | 5 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | push_the_plate_to_the_front_of_the_stove |
| libero_goal | 6 | 0 | 20 | 39 | 1.95 | True | False | 0.00000 | put_the_cream_cheese_in_the_bowl |
| libero_goal | 7 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | turn_on_the_stove |
| libero_goal | 8 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | put_the_bowl_on_the_plate |
| libero_goal | 9 | 0 | 8 | 27 | 1.35 | True | True | 0.00000 | put_the_wine_bottle_on_the_rack |
| libero_90 | 0 | 0 | 12 | 31 | 1.55 | True | False | 0.00000 | KITCHEN_SCENE10_close_the_top_drawer_of_the_cabinet |
| libero_90 | 1 | 0 | 10 | 29 | 1.45 | True | True | 0.00000 | KITCHEN_SCENE10_close_the_top_drawer_of_the_cabinet_and_put_the_black_bowl_on_top_of_it |
| libero_90 | 2 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | KITCHEN_SCENE10_put_the_black_bowl_in_the_top_drawer_of_the_cabinet |
| libero_90 | 3 | 0 | 10 | 29 | 1.45 | True | True | 0.00000 | KITCHEN_SCENE10_put_the_butter_at_the_back_in_the_top_drawer_of_the_cabinet_and_close_it |
| libero_90 | 4 | 0 | 5 | 24 | 1.2 | True | True | 0.00000 | KITCHEN_SCENE10_put_the_butter_at_the_front_in_the_top_drawer_of_the_cabinet_and_close_it |
| libero_90 | 5 | 0 | 9 | 28 | 1.4 | True | True | 0.00000 | KITCHEN_SCENE10_put_the_chocolate_pudding_in_the_top_drawer_of_the_cabinet_and_close_it |
| libero_90 | 6 | 0 | 8 | 27 | 1.35 | True | True | 0.00000 | KITCHEN_SCENE1_open_the_bottom_drawer_of_the_cabinet |
| libero_90 | 7 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | KITCHEN_SCENE1_open_the_top_drawer_of_the_cabinet |
| libero_90 | 8 | 0 | 21 | 40 | 2.0 | True | False | 0.00000 | KITCHEN_SCENE1_open_the_top_drawer_of_the_cabinet_and_put_the_bowl_in_it |
| libero_90 | 9 | 0 | 19 | 38 | 1.9 | True | False | 0.00000 | KITCHEN_SCENE1_put_the_black_bowl_on_the_plate |
| libero_90 | 10 | 0 | 12 | 31 | 1.55 | True | False | 0.00000 | KITCHEN_SCENE1_put_the_black_bowl_on_top_of_the_cabinet |
| libero_90 | 11 | 0 | 9 | 28 | 1.4 | True | True | 0.00000 | KITCHEN_SCENE2_open_the_top_drawer_of_the_cabinet |
| libero_90 | 12 | 0 | 10 | 29 | 1.45 | True | True | 0.00000 | KITCHEN_SCENE2_put_the_black_bowl_at_the_back_on_the_plate |
| libero_90 | 13 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | KITCHEN_SCENE2_put_the_black_bowl_at_the_front_on_the_plate |
| libero_90 | 14 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | KITCHEN_SCENE2_put_the_middle_black_bowl_on_the_plate |
| libero_90 | 15 | 0 | 20 | 39 | 1.95 | True | False | 0.00000 | KITCHEN_SCENE2_put_the_middle_black_bowl_on_top_of_the_cabinet |
| libero_90 | 16 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | KITCHEN_SCENE2_stack_the_black_bowl_at_the_front_on_the_black_bowl_in_the_middle |
| libero_90 | 17 | 0 | 12 | 31 | 1.55 | True | False | 0.00000 | KITCHEN_SCENE2_stack_the_middle_black_bowl_on_the_back_black_bowl |
| libero_90 | 18 | 0 | 21 | 40 | 2.0 | True | False | 0.00054 | KITCHEN_SCENE3_put_the_frying_pan_on_the_stove |
| libero_90 | 19 | 0 | 15 | 34 | 1.7 | True | False | 0.00054 | KITCHEN_SCENE3_put_the_moka_pot_on_the_stove |
| libero_90 | 20 | 0 | 13 | 32 | 1.6 | True | False | 0.00054 | KITCHEN_SCENE3_turn_on_the_stove |
| libero_90 | 21 | 0 | 11 | 30 | 1.5 | True | False | 0.00054 | KITCHEN_SCENE3_turn_on_the_stove_and_put_the_frying_pan_on_it |
| libero_90 | 22 | 0 | 15 | 34 | 1.7 | True | False | 0.00000 | KITCHEN_SCENE4_close_the_bottom_drawer_of_the_cabinet |
| libero_90 | 23 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | KITCHEN_SCENE4_close_the_bottom_drawer_of_the_cabinet_and_open_the_top_drawer |
| libero_90 | 24 | 0 | 7 | 26 | 1.3 | True | True | 0.00000 | KITCHEN_SCENE4_put_the_black_bowl_in_the_bottom_drawer_of_the_cabinet |
| libero_90 | 25 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | KITCHEN_SCENE4_put_the_black_bowl_on_top_of_the_cabinet |
| libero_90 | 26 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | KITCHEN_SCENE4_put_the_wine_bottle_in_the_bottom_drawer_of_the_cabinet |
| libero_90 | 27 | 0 | 19 | 38 | 1.9 | True | False | 0.00000 | KITCHEN_SCENE4_put_the_wine_bottle_on_the_wine_rack |
| libero_90 | 28 | 0 | 9 | 28 | 1.4 | True | True | 0.00017 | KITCHEN_SCENE5_close_the_top_drawer_of_the_cabinet |
| libero_90 | 29 | 0 | 12 | 31 | 1.55 | True | False | 0.00017 | KITCHEN_SCENE5_put_the_black_bowl_in_the_top_drawer_of_the_cabinet |
| libero_90 | 30 | 0 | 11 | 30 | 1.5 | True | False | 0.00017 | KITCHEN_SCENE5_put_the_black_bowl_on_the_plate |
| libero_90 | 31 | 0 | 18 | 37 | 1.85 | True | False | 0.00017 | KITCHEN_SCENE5_put_the_black_bowl_on_top_of_the_cabinet |
| libero_90 | 32 | 0 | 12 | 31 | 1.55 | True | False | 0.00017 | KITCHEN_SCENE5_put_the_ketchup_in_the_top_drawer_of_the_cabinet |
| libero_90 | 33 | 0 | 15 | 34 | 1.7 | True | False | 0.00000 | KITCHEN_SCENE6_close_the_microwave |
| libero_90 | 34 | 0 | 12 | 31 | 1.55 | True | False | 0.00000 | KITCHEN_SCENE6_put_the_yellow_and_white_mug_to_the_front_of_the_white_mug |
| libero_90 | 35 | 0 | 21 | 40 | 2.0 | True | False | 0.00000 | KITCHEN_SCENE7_open_the_microwave |
| libero_90 | 36 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | KITCHEN_SCENE7_put_the_white_bowl_on_the_plate |
| libero_90 | 37 | 0 | 8 | 27 | 1.35 | True | True | 0.00000 | KITCHEN_SCENE7_put_the_white_bowl_to_the_right_of_the_plate |
| libero_90 | 38 | 0 | 10 | 29 | 1.45 | True | True | 0.00054 | KITCHEN_SCENE8_put_the_right_moka_pot_on_the_stove |
| libero_90 | 39 | 0 | 10 | 29 | 1.45 | True | True | 0.00054 | KITCHEN_SCENE8_turn_off_the_stove |
| libero_90 | 40 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | KITCHEN_SCENE9_put_the_frying_pan_on_the_cabinet_shelf |
| libero_90 | 41 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | KITCHEN_SCENE9_put_the_frying_pan_on_top_of_the_cabinet |
| libero_90 | 42 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | KITCHEN_SCENE9_put_the_frying_pan_under_the_cabinet_shelf |
| libero_90 | 43 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | KITCHEN_SCENE9_put_the_white_bowl_on_top_of_the_cabinet |
| libero_90 | 44 | 0 | 7 | 26 | 1.3 | True | True | 0.00000 | KITCHEN_SCENE9_turn_on_the_stove |
| libero_90 | 45 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | KITCHEN_SCENE9_turn_on_the_stove_and_put_the_frying_pan_on_it |
| libero_90 | 46 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE1_pick_up_the_alphabet_soup_and_put_it_in_the_basket |
| libero_90 | 47 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE1_pick_up_the_cream_cheese_box_and_put_it_in_the_basket |
| libero_90 | 48 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE1_pick_up_the_ketchup_and_put_it_in_the_basket |
| libero_90 | 49 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE1_pick_up_the_tomato_sauce_and_put_it_in_the_basket |
| libero_90 | 50 | 0 | 21 | 40 | 2.0 | True | False | 0.00005 | LIVING_ROOM_SCENE2_pick_up_the_alphabet_soup_and_put_it_in_the_basket |
| libero_90 | 51 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE2_pick_up_the_butter_and_put_it_in_the_basket |
| libero_90 | 52 | 0 | 21 | 40 | 2.0 | True | False | 0.00005 | LIVING_ROOM_SCENE2_pick_up_the_milk_and_put_it_in_the_basket |
| libero_90 | 53 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE2_pick_up_the_orange_juice_and_put_it_in_the_basket |
| libero_90 | 54 | 0 | 23 | 42 | 2.1 | True | False | 0.00005 | LIVING_ROOM_SCENE2_pick_up_the_tomato_sauce_and_put_it_in_the_basket |
| libero_90 | 55 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE3_pick_up_the_alphabet_soup_and_put_it_in_the_tray |
| libero_90 | 56 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE3_pick_up_the_butter_and_put_it_in_the_tray |
| libero_90 | 57 | 0 | 18 | 37 | 1.85 | True | False | 0.00005 | LIVING_ROOM_SCENE3_pick_up_the_cream_cheese_and_put_it_in_the_tray |
| libero_90 | 58 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE3_pick_up_the_ketchup_and_put_it_in_the_tray |
| libero_90 | 59 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE3_pick_up_the_tomato_sauce_and_put_it_in_the_tray |
| libero_90 | 60 | 0 | 22 | 41 | 2.05 | True | False | 0.00000 | LIVING_ROOM_SCENE4_pick_up_the_black_bowl_on_the_left_and_put_it_in_the_tray |
| libero_90 | 61 | 0 | 15 | 34 | 1.7 | True | False | 0.00000 | LIVING_ROOM_SCENE4_pick_up_the_chocolate_pudding_and_put_it_in_the_tray |
| libero_90 | 62 | 0 | 15 | 34 | 1.7 | True | False | 0.00000 | LIVING_ROOM_SCENE4_pick_up_the_salad_dressing_and_put_it_in_the_tray |
| libero_90 | 63 | 0 | 8 | 27 | 1.35 | True | True | 0.00000 | LIVING_ROOM_SCENE4_stack_the_left_bowl_on_the_right_bowl_and_place_them_in_the_tray |
| libero_90 | 64 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | LIVING_ROOM_SCENE4_stack_the_right_bowl_on_the_left_bowl_and_place_them_in_the_tray |
| libero_90 | 65 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | LIVING_ROOM_SCENE5_put_the_red_mug_on_the_left_plate |
| libero_90 | 66 | 0 | 9 | 28 | 1.4 | True | True | 0.00000 | LIVING_ROOM_SCENE5_put_the_red_mug_on_the_right_plate |
| libero_90 | 67 | 0 | 10 | 29 | 1.45 | True | True | 0.00000 | LIVING_ROOM_SCENE5_put_the_white_mug_on_the_left_plate |
| libero_90 | 68 | 0 | 10 | 29 | 1.45 | True | True | 0.00000 | LIVING_ROOM_SCENE5_put_the_yellow_and_white_mug_on_the_right_plate |
| libero_90 | 69 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | LIVING_ROOM_SCENE6_put_the_chocolate_pudding_to_the_left_of_the_plate |
| libero_90 | 70 | 0 | 8 | 27 | 1.35 | True | True | 0.00000 | LIVING_ROOM_SCENE6_put_the_chocolate_pudding_to_the_right_of_the_plate |
| libero_90 | 71 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | LIVING_ROOM_SCENE6_put_the_red_mug_on_the_plate |
| libero_90 | 72 | 0 | 15 | 34 | 1.7 | True | False | 0.00000 | LIVING_ROOM_SCENE6_put_the_white_mug_on_the_plate |
| libero_90 | 73 | 0 | 18 | 37 | 1.85 | True | False | 0.00000 | STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_front_compartment_of_the_caddy |
| libero_90 | 74 | 0 | 12 | 31 | 1.55 | True | False | 0.00000 | STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_left_compartment_of_the_caddy |
| libero_90 | 75 | 0 | 10 | 29 | 1.45 | True | True | 0.00000 | STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_right_compartment_of_the_caddy |
| libero_90 | 76 | 0 | 16 | 35 | 1.75 | True | False | 0.00000 | STUDY_SCENE1_pick_up_the_yellow_and_white_mug_and_place_it_to_the_right_of_the_caddy |
| libero_90 | 77 | 0 | 16 | 35 | 1.75 | True | False | 0.00000 | STUDY_SCENE2_pick_up_the_book_and_place_it_in_the_back_compartment_of_the_caddy |
| libero_90 | 78 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | STUDY_SCENE2_pick_up_the_book_and_place_it_in_the_front_compartment_of_the_caddy |
| libero_90 | 79 | 0 | 15 | 34 | 1.7 | True | False | 0.00000 | STUDY_SCENE2_pick_up_the_book_and_place_it_in_the_left_compartment_of_the_caddy |
| libero_90 | 80 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | STUDY_SCENE2_pick_up_the_book_and_place_it_in_the_right_compartment_of_the_caddy |
| libero_90 | 81 | 0 | 8 | 27 | 1.35 | True | True | 0.00000 | STUDY_SCENE3_pick_up_the_book_and_place_it_in_the_front_compartment_of_the_caddy |
| libero_90 | 82 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | STUDY_SCENE3_pick_up_the_book_and_place_it_in_the_left_compartment_of_the_caddy |
| libero_90 | 83 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | STUDY_SCENE3_pick_up_the_book_and_place_it_in_the_right_compartment_of_the_caddy |
| libero_90 | 84 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | STUDY_SCENE3_pick_up_the_red_mug_and_place_it_to_the_right_of_the_caddy |
| libero_90 | 85 | 0 | 10 | 29 | 1.45 | True | True | 0.00000 | STUDY_SCENE3_pick_up_the_white_mug_and_place_it_to_the_right_of_the_caddy |
| libero_90 | 86 | 0 | 13 | 32 | 1.6 | True | False | 0.00000 | STUDY_SCENE4_pick_up_the_book_in_the_middle_and_place_it_on_the_cabinet_shelf |
| libero_90 | 87 | 0 | 18 | 37 | 1.85 | True | False | 0.00000 | STUDY_SCENE4_pick_up_the_book_on_the_left_and_place_it_on_top_of_the_shelf |
| libero_90 | 88 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | STUDY_SCENE4_pick_up_the_book_on_the_right_and_place_it_on_the_cabinet_shelf |
| libero_90 | 89 | 0 | 11 | 30 | 1.5 | True | False | 0.00000 | STUDY_SCENE4_pick_up_the_book_on_the_right_and_place_it_under_the_cabinet_shelf |
| libero_10 | 0 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE2_put_both_the_alphabet_soup_and_the_tomato_sauce_in_the_basket |
| libero_10 | 1 | 0 | 18 | 37 | 1.85 | True | False | 0.00005 | LIVING_ROOM_SCENE2_put_both_the_cream_cheese_box_and_the_butter_in_the_basket |
| libero_10 | 2 | 0 | 15 | 34 | 1.7 | True | False | 0.00054 | KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it |
| libero_10 | 3 | 0 | 14 | 33 | 1.65 | True | False | 0.00000 | KITCHEN_SCENE4_put_the_black_bowl_in_the_bottom_drawer_of_the_cabinet_and_close_it |
| libero_10 | 4 | 0 | 16 | 35 | 1.75 | True | False | 0.00000 | LIVING_ROOM_SCENE5_put_the_white_mug_on_the_left_plate_and_put_the_yellow_and_white_mug_on_the_right_plate |
| libero_10 | 5 | 0 | 20 | 39 | 1.95 | True | False | 0.00000 | STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_back_compartment_of_the_caddy |
| libero_10 | 6 | 0 | 17 | 36 | 1.8 | True | False | 0.00000 | LIVING_ROOM_SCENE6_put_the_white_mug_on_the_plate_and_put_the_chocolate_pudding_to_the_right_of_the_plate |
| libero_10 | 7 | 0 | 16 | 35 | 1.75 | True | False | 0.00005 | LIVING_ROOM_SCENE1_put_both_the_alphabet_soup_and_the_cream_cheese_box_in_the_basket |
| libero_10 | 8 | 0 | 15 | 34 | 1.7 | True | False | 0.00054 | KITCHEN_SCENE8_put_both_moka_pots_on_the_stove |
| libero_10 | 9 | 0 | 20 | 39 | 1.95 | True | False | 0.00000 | KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it |
