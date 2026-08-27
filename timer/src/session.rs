use crate::actions::OutputAction;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone, Debug, Default)]
pub enum Session {
    /// Time is ticking
    Ongoing {
        start_time: jiff::Zoned,
        duration: jiff::Span,
    },
    #[default]
    /// No tracking
    Stopped,
}

impl Session {
    pub fn update_at_time(
        &mut self,
        session_action: SessionAction,
        now: &jiff::Zoned,
    ) -> Result<Option<OutputAction>, crate::errors::Error> {
        let old_session = std::mem::take(self);
        let result = match session_action {
            SessionAction::Start { duration } => {
                let start = now.clone();
                let mut end = now.clone() + duration;

                let limit = start
                    .with()
                    .time(jiff::civil::time(21, 30, 0, 0))
                    .build()
                    .unwrap();

                // clamp to 21:30 when it makes sense
                if end > limit && now < limit {
                    end = limit
                }

                let duration = start.until(&end).unwrap();

                Ok((
                    Session::Ongoing {
                        start_time: start,
                        duration,
                    },
                    Some(OutputAction::SessionStart),
                ))
            }
            SessionAction::Stop => Ok((Session::Stopped, Some(OutputAction::SessionEnd))),
            SessionAction::None => match old_session.status_at_time(now) {
                SessionStatus::Ongoing { end_time, .. } => {
                    if now < end_time {
                        Ok((old_session, None))
                    } else {
                        Ok((Session::Stopped {}, Some(OutputAction::SessionEnd)))
                    }
                }
                SessionStatus::Stopped => Ok((old_session, None)),
            },
        };
        let (new_session, output_action) = result?;
        *self = new_session;
        Ok(output_action)
    }

    pub fn status_at_time(&self, now: &jiff::Zoned) -> SessionStatus {
        // this function should never be expensive to compute
        match &self {
            Session::Ongoing {
                start_time,
                duration,
            } => {
                let end_time = start_time.clone() + *duration;
                SessionStatus::Ongoing {
                    duration: *duration,
                    start_time: start_time.clone(),
                    until_end: now.until(&end_time).unwrap(),
                    end_time,
                }
            }
            Session::Stopped => SessionStatus::Stopped,
        }
    }
}

/// Computed [`Session`] information.
#[expect(clippy::large_enum_variant)] // ~250 bytes should be ok
pub enum SessionStatus {
    Ongoing {
        duration: jiff::Span,
        start_time: jiff::Zoned,
        end_time: jiff::Zoned,
        until_end: jiff::Span,
    },
    Stopped,
}

pub enum SessionAction {
    Start { duration: jiff::Span },
    Stop,
    None,
}
