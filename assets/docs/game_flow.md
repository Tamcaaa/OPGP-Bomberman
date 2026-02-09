flowchart TD
    subgraph MainApp["BomberManApp.py"]
        A["run()"] --> B["get_events()"]
        B --> C["state_stack.top.handle_events()"]
        A --> D["update()"]
        D --> E["state_stack.top.update()"]
        A --> F["render()"]
        F --> G["state_stack.top.render()"]
    end

    subgraph StateManagement["state_manager.py"]
        H --> I["import module/class"]
        I --> J["new_state.enter_state()"]
        J --> K["state_stack.push()"]
    end

    subgraph TestFieldState["test_field.py"]
        C --> L{KEYDOWN/UP}
        L -->|P1 keys| P1["Player1.held_down_keys"]
        L -->|P2 keys| P2["Player2.held_down_keys"]
        L -->|P key| H

        E --> M["Player.handle_queued_keys()"]
        M --> N["Player.move / deploy_bomb()"]
        E --> O["Player.update_animation + powerups"]
        E --> P["bomb_group.update -> Bomb.explode"]
        P --> Q["Explosion sprites added"]
        E --> R["check_hit per player"]
        R -->|health 0| H
        E --> S["destroy_tile if brick"]
        S --> T["spawn/reveal PowerUp"]
        E --> U["check_powerup_collisions -> apply_effect"]
        E --> V["powerup_group.update expiry"]
        E --> W["check_trap_collisions()"]

        G --> X["draw_grid/walls/bg/UI"]
        G --> Y["bomb_group.draw()"]
        G --> Z["explosion_group.draw()"]
        G --> AA["powerup_group.draw()"]
        G --> AB["draw_players (+hats)"]
    end
