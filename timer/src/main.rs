use std::path::PathBuf;

use clap::Parser;
use timer::{
    actions::{ActionRunner, ScriptActionRunnerImpl},
    cli::Command,
    session::{SessionAction, SessionStatus},
    state::read_state,
};

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

fn main() {
    let cli = timer::cli::Cli::parse();

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

    let session_action = match cli.command {
        Command::Start { duration } => SessionAction::Start {
            duration: jiff::Span::new().minutes(duration),
        },
        Command::Stop {} => SessionAction::Stop,
        Command::Status {} => SessionAction::None,
        Command::Short {} => SessionAction::None,
    };

    let action = state
        .current_session
        .update(session_action)
        .unwrap_or_else(|e| panic!("{e}"));
    if let Some(action) = action {
        runner.run(action);
    }

    match cli.command {
        Command::Short {} => match state.current_session.status() {
            SessionStatus::Ongoing { until_end, .. } => {
                println!("{}", format_span(until_end));
            }
            SessionStatus::Stopped => println!("--:--"),
        },
        _ => {
            println!("SESSION");
            match state.current_session.status() {
                SessionStatus::Ongoing {
                    until_end,
                    duration,
                    start_time,
                    end_time,
                    ..
                } => {
                    println!(
                        "{} -> {} ({:#})",
                        start_time.strftime("%H:%M"),
                        end_time.strftime("%H:%M"),
                        duration.round(jiff::Unit::Minute).unwrap(),
                    );
                    println!(
                        "{:#} remaining",
                        until_end.round(jiff::Unit::Minute).unwrap()
                    );
                }
                SessionStatus::Stopped => {
                    println!("no tracking")
                }
            }
        }
    }

    if cli.verbose {
        println!("{state:#?}");
    }

    std::fs::write(state_file, serde_json::to_string(&state).unwrap()).unwrap();
}
