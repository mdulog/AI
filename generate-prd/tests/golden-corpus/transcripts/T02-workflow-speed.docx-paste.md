Customer call notes — Loopr — Northwind Freight — pasted from Word doc

So um, thanks for jumping on. I wanted to understand how your team is using Loopr day to day and where it's, uh, where it's working and where it isn't. Yeah, sure. So we've been on it for about six weeks. The team is — I mean, the dispatch team — they use it constantly. Like, it's open all day on three monitors. That's the good part.

The bad part is, um, it's slow. Not slow like broken-slow, just — every action takes a beat. You click a shipment, there's a half-second before the panel opens. You drag a route, there's another half-second. I— I mean, individually it's nothing. But you do that two hundred times in a shift and it adds up. People notice.

Right, that latency story is something we've been digging into. Can you tell me, um, is it worse at any particular time of day? Yeah, mornings are the worst. Like 7 to 9 AM when everyone is planning the day. It's bad enough that two of my leads have started doing route planning in the old spreadsheet first and then just, you know, copy-pasting the final into Loopr. Which kind of defeats the point.

Onboarding, that's a separate thing — the onboarding was confusing. We had a lot of, uh, "where is X" moments in the first week. But people got past it. The speed issue is the one that hasn't gone away. It's actually, I think, the thing that would make us churn if we churn. The pricing is fine, the features are fine, it's just — wait, sorry, it's just the workflow speed.

Got it. Um, if we shipped a perf release that cut interaction latency by half — like sub-200ms on the common actions — does that solve it? Yeah, that would, I mean, that would change everything for us. The team has muscle memory from faster tools. Loopr feels like it's, um, like it's making them wait. Take that away and we'd be advocates.

One more thing — and this is more of a wish-list — the bulk edit. When I select fifty shipments and change the status, it takes like, I don't know, eight seconds? Maybe ten? My ops lead literally times it. He's been clocking it. So, you know, bulk operations specifically are where it falls down hardest.

Yeah, bulk is on our radar. We're looking at moving those to a background job with optimistic UI. Does that, um, would that read as "fast" to your team even if the actual write took the same time? Honestly? Yes. If the UI says "done" and the change shows up, nobody is checking the database. They just want to keep moving.

Okay this has been super helpful. The onboarding piece — quick follow-up — was that, uh, was that the import flow specifically? Or just generally? Generally. The import flow was actually fine for us because we had a clean CSV. It was more like, where do I find settings, where do I invite a user, where do I see the audit log. Discoverability stuff. We figured it out but it took longer than it should have.

Cool. Last question — anything else that's, um, top of mind? No I think speed is, like, the whole thing. Fix speed and we're, we're locked in for renewal. Don't fix it and we'll be having a different conversation in March.
