//
//  DistanceWidget.swift
//  "How Far Are You?": Baby pink themed WidgetKit widget (Pink for to honor Mean Girls)
//
//  Drop this file into a WidgetKit Extension target in Xcode.
//  (File > New > Target > Widget Extension)
//
//  This widget calls your Flask backend (the distance_tracker.py logic,
//  exposed as a small API) to get each family member's distance from you,
//  then renders it in a baby pink card.
//
//  Replace `apiURL` with your backend's real URL once deployed, you can get free API's or use cluade to help you vibe code it.
//

import WidgetKit
import SwiftUI

// MARK: Data model returned by your Flask API
// Matches tracker.widget_summary() from distance_tracker.py
struct Person: Identifiable, Codable {
    var id: String { name }
    let name: String
    let emoji: String
    let relationship: String
    let distance: Double?
    let unit: String
}

// MARK: Timeline entry
struct DistanceEntry: TimelineEntry {
    let date: Date
    let people: [Person]
}

// MARK: Timeline provider (fetches data + refreshes widget)
struct DistanceProvider: TimelineProvider {

    // Point this at your deployed Flask endpoint, ex
    // https://yourapp.onrender.com/widget_summary?unit=mi
    let apiURL = URL(string: "https://YOUR_BACKEND_URL/widget_summary?unit=mi")!

    func placeholder(in context: Context) -> DistanceEntry {
        DistanceEntry(date: Date(), people: samplePeople)
    }

    func getSnapshot(in context: Context, completion: @escaping (DistanceEntry) -> Void) {
        completion(DistanceEntry(date: Date(), people: samplePeople))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<DistanceEntry>) -> Void) {
        fetchPeople { people in
            let entry = DistanceEntry(date: Date(), people: people ?? samplePeople)
            // Refresh every 15 minutes
            let nextUpdate = Calendar.current.date(byAdding: .minute, value: 15, to: Date())!
            let timeline = Timeline(entries: [entry], policy: .after(nextUpdate))
            completion(timeline)
        }
    }

    private func fetchPeople(completion: @escaping ([Person]?) -> Void) {
        URLSession.shared.dataTask(with: apiURL) { data, _, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            let decoded = try? JSONDecoder().decode([Person].self, from: data)
            completion(decoded)
        }.resume()
    }

    private var samplePeople: [Person] {
        [
            Person(name: "Mom", emoji: "🥰", relationship: "Mother", distance: 2445, unit: "mi"),
            Person(name: "Dad", emoji: "🤗", relationship: "Father", distance: 711, unit: "mi"),
            Person(name: "Lily", emoji: "💕", relationship: "Sister", distance: 3461, unit: "mi")
        ]
    }
}

// MARK: Baby pink color palette
extension Color {
    static let babyPinkBackground = Color(red: 0.98, green: 0.92, blue: 0.94)  // #FBEAF0
    static let babyPinkCard = Color(red: 0.96, green: 0.75, blue: 0.82)        // #F4C0D1
    static let babyPinkAccent = Color(red: 0.83, green: 0.33, blue: 0.49)      // #D4537E
    static let babyPinkText = Color(red: 0.29, green: 0.08, blue: 0.16)        // #4B1528
}

// MARK: Widget view
struct DistanceWidgetView: View {
    var entry: DistanceEntry

    var body: some View {
        ZStack {
            Color.babyPinkBackground

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("How far are you?")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.babyPinkAccent)
                    Spacer()
                    Image(systemName: "mappin.and.ellipse")
                        .foregroundColor(.babyPinkAccent)
                        .font(.system(size: 14))
                }

                ForEach(entry.people.prefix(3)) { person in
                    HStack {
                        Text(person.emoji)
                            .font(.system(size: 16))
                        Text(person.name)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.babyPinkText)
                        Spacer()
                        if let distance = person.distance {
                            Text("\(Int(distance)) \(person.unit)")
                                .font(.system(size: 12))
                                .foregroundColor(.babyPinkAccent)
                        } else {
                            Text("—")
                                .font(.system(size: 12))
                                .foregroundColor(.babyPinkAccent)
                        }
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 6)
                    .background(Color.babyPinkCard.opacity(0.5))
                    .cornerRadius(8)
                }
            }
            .padding(12)
        }
    }
}

// MARK: Widget configuration
struct DistanceWidget: Widget {
    let kind: String = "DistanceWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: DistanceProvider()) { entry in
            DistanceWidgetView(entry: entry)
                .containerBackground(Color.babyPinkBackground, for: .widget)
        }
        .configurationDisplayName("How Far Are You?")
        .description("See how far your family is from you, right now.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

// MARK: Preview
struct DistanceWidget_Previews: PreviewProvider {
    static var previews: some View {
        DistanceWidgetView(entry: DistanceEntry(
            date: Date(),
            people: [
                Person(name: "Mom", emoji: "🥰", relationship: "Mother", distance: 2445, unit: "mi"),
                Person(name: "Dad", emoji: "🤗", relationship: "Father", distance: 711, unit: "mi"),
                Person(name: "Lily", emoji: "💕", relationship: "Sister", distance: 3461, unit: "mi")
            ]
        ))
        .previewContext(WidgetPreviewContext(family: .systemMedium))
    }
}
