#[derive(Debug)]
pub enum OutputAction {
    SessionStart,
    SessionEnd,
}

pub trait ActionRunner {
    fn run(&mut self, action: OutputAction);
}

#[derive(Default)]
pub struct ScriptActionRunnerImpl {}

impl ActionRunner for ScriptActionRunnerImpl {
    fn run(&mut self, action: OutputAction) {
        let arg = match action {
            OutputAction::SessionStart => "start",
            OutputAction::SessionEnd => "finish",
        };
        std::process::Command::new("timer-action.sh")
            .arg(arg)
            .output()
            .unwrap();
    }
}
