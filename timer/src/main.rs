use std::path::PathBuf;

use clap::Parser;
use timer::{
    actions::{ActionRunner, OutputAction, ScriptActionRunnerImpl},
    cli::{Args, Command},
    session::{SessionAction, SessionStatus},
    state::{State, read_state},
};

fn main() {
    let args = timer::cli::Args::parse();

    let state_dir =
        PathBuf::from(std::env::var("XDG_DATA_HOME").expect("XDG_DATA_HOME should be set"))
            .join("timer");
    let _ = std::fs::create_dir(&state_dir);
    let state_file = if cfg!(not(debug_assertions)) {
        state_dir.join("timer.json")
    } else {
        state_dir.join("timer-staging.json")
    };

    let mut state = read_state(&state_file).unwrap_or_default();
    let mut runner = ScriptActionRunnerImpl::default();

    let now = jiff::Zoned::now();
    let output = run(
        AppInput {
            state: &mut state,
            now: &now,
            args,
        },
        &mut std::io::stdout(),
    );

    if let Some(action) = output.action {
        runner.run(action);
        std::fs::write(state_file, serde_json::to_string(&state).unwrap()).unwrap();
    }
}

struct AppInput<'a> {
    state: &'a mut State,
    now: &'a jiff::Zoned,
    args: Args,
}

struct AppOutput {
    action: Option<OutputAction>,
}

fn format_span(span: jiff::Span) -> String {
    let rounded = span
        .round(jiff::SpanRound::new().largest(jiff::Unit::Minute))
        .unwrap();
    format!(
        "{:>02}:{:>02}",
        rounded.get_minutes(),
        rounded.get_seconds()
    )
}

/// Core app logic.
fn run(input: AppInput, stdout: &mut impl std::io::Write) -> AppOutput {
    let AppInput { state, now, args } = input;

    if args.verbose {
        writeln!(stdout, "input state: {state:#?}").unwrap();
    }

    let session_action = match args.command {
        Command::Start { duration } => SessionAction::Start {
            duration: jiff::Span::new().minutes(duration),
        },
        Command::Stop {} => SessionAction::Stop,
        Command::Status {} => SessionAction::None,
        Command::Short {} => SessionAction::None,
    };

    let action = state
        .current_session
        .update_at_time(session_action, now)
        .unwrap_or_else(|e| panic!("{e}"));

    match args.command {
        Command::Short {} => match state.current_session.status_at_time(now) {
            SessionStatus::Ongoing { until_end, .. } => {
                writeln!(stdout, "{}", format_span(until_end)).unwrap();
            }
            SessionStatus::Stopped => writeln!(stdout, "--:--").unwrap(),
        },
        _ => {
            writeln!(stdout, "SESSION").unwrap();
            match state.current_session.status_at_time(now) {
                SessionStatus::Ongoing {
                    until_end,
                    duration,
                    start_time,
                    end_time,
                    ..
                } => {
                    writeln!(
                        stdout,
                        "{} -> {} ({:#})",
                        start_time.strftime("%H:%M"),
                        end_time.strftime("%H:%M"),
                        duration.round(jiff::Unit::Minute).unwrap(),
                    )
                    .unwrap();
                    writeln!(
                        stdout,
                        "{:#} remaining",
                        until_end.round(jiff::Unit::Minute).unwrap()
                    )
                    .unwrap();
                }
                SessionStatus::Stopped => writeln!(stdout, "no tracking").unwrap(),
            }
        }
    }

    if args.verbose {
        writeln!(stdout, "output state: {state:#?}").unwrap();
        writeln!(stdout, "action: {action:#?}").unwrap();
    }

    AppOutput { action }
}
