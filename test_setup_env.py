from dotenv import dotenv_values

import setup_env


def test_setup_writes_settings_without_printing_the_token(tmp_path, monkeypatch, capsys):
    secret = "demo-secret-value"
    env_path = tmp_path / ".env"
    monkeypatch.setattr(setup_env, "ENV_PATH", env_path)

    def fake_input(prompt: str) -> str:
        return "https://demo.example.com" if "workspace URL" in prompt else ""

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(setup_env, "getpass", lambda _prompt: secret)

    setup_env.main()

    output = capsys.readouterr().out
    values = dotenv_values(env_path)
    assert values["APP_DATABRICKS_HOST"] == "https://demo.example.com"
    assert values["APP_DATABRICKS_TOKEN"] == secret
    assert values["APP_DATABRICKS_MODEL"] == setup_env.DEFAULT_MODEL
    assert secret not in output
    assert "saved" in output


def test_setup_writes_to_project_only_path(tmp_path):
    env_path = tmp_path / ".env"
    setup_env.write_project_env(
        "https://demo.example.com", "another-secret", "test-model", env_path
    )
    assert env_path.is_file()
    assert dotenv_values(env_path) == {
        "APP_DATABRICKS_HOST": "https://demo.example.com",
        "APP_DATABRICKS_TOKEN": "another-secret",
        "APP_DATABRICKS_MODEL": "test-model",
    }
