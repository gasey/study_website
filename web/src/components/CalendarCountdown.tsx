import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  calendarPersonal,
  indiaToday,
  dayNumber,
  type CalendarEvent,
} from "../lib/calendar";
export default function CalendarCountdown() {
  const [event, setEvent] = useState<CalendarEvent | null>(null);
  useEffect(() => {
    let live = true,
      generation = 0;
    const load = () => {
      const n = ++generation;
      calendarPersonal()
        .then((p) => {
          if (live && n === generation) setEvent(p.upcoming);
        })
        .catch(() => {
          if (live && n === generation) setEvent(null);
        });
    };
    load();
    window.addEventListener("ism-calendar-change", load);
    window.addEventListener("ism-auth-change", load);
    return () => {
      live = false;
      window.removeEventListener("ism-calendar-change", load);
      window.removeEventListener("ism-auth-change", load);
    };
  }, []);
  return (
    <Link
      to={event ? "/calendar?event=" + event.id : "/calendar"}
      className="block rounded-panel bg-ink p-4 text-paper"
    >
      <span className="text-[12px] font-semibold text-[#D8A33A]">
        Your exam calendar
      </span>
      {event?.starts_on ? (
        <>
          <span className="mt-2 block font-display text-[35px] leading-tight">
            {Math.max(0, dayNumber(event.starts_on) - dayNumber(indiaToday()))}{" "}
            days
          </span>
          <span className="mt-2 block text-[14px]">{event.title}</span>
          <span className="mt-2 block text-[12px] text-[#D9D0BF]">
            Confirm the official notice →
          </span>
        </>
      ) : (
        <>
          <span className="mt-2 block font-display text-[23px]">
            What’s coming up
          </span>
          <span className="mt-2 block text-[13px] text-[#D9D0BF]">
            Follow exams, save dates and choose inbox reminders →
          </span>
        </>
      )}
    </Link>
  );
}
